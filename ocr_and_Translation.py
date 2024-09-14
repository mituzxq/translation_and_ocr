import tkinter as tk
from tkinter import Toplevel, filedialog
from PIL import Image, ImageTk, ImageEnhance
import uuid
import pyautogui
import pytesseract
import argostranslate.translate
import keyboard
import asyncio
import threading
import concurrent.futures
import queue
import functools

executor = concurrent.futures.ThreadPoolExecutor()
installed_languages = []

ocr_cache = {}
translation_cache = {}

def initialize_libraries():
    global installed_languages
    try:
        installed_languages = argostranslate.translate.get_installed_languages()
        pytesseract.image_to_string(Image.new('RGB', (10, 10)))
    except Exception as e:
        print(f"Initialization error: {e}")

def preprocess_image(image):
    gray_image = image.convert('L')
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced_image = enhancer.enhance(2)
    return enhanced_image

def cached_ocr(img, lang):
    img_id = functools.reduce(lambda a, b: a ^ b, img.tobytes())

    if (img_id, lang) in ocr_cache:
        return ocr_cache[(img_id, lang)]

    text = pytesseract.image_to_string(img, lang)
    ocr_cache[(img_id, lang)] = text
    return text

async def translate_text(text, from_lang_code, to_lang_code):
    try:
        if from_lang_code == to_lang_code:
            return text

        def get_language(lang_code):
            return next((lang for lang in installed_languages if lang.code == lang_code), None)

        from_lang = get_language(from_lang_code)
        to_lang = get_language(to_lang_code)

        if not from_lang or not to_lang:
            return "Translation failed: Language package not found."

        if (from_lang_code, to_lang_code) in [('zh', 'en'), ('en', 'zh')]:
            translated_text = from_lang.get_translation(to_lang).translate(text)
            return translated_text
        else:
            return "Translation only supported between Chinese and English."
    except Exception as e:
        return f"Translation error: {e}"

def translate_worker(text, from_lang_code, to_lang_code, result, index):
    translated_text = asyncio.run(translate_text(text, from_lang_code, to_lang_code))
    result[index] = translated_text

def translate_in_parallel(texts, from_lang_code, to_lang_code):
    translations = [None] * len(texts)
    threads = []

    for i, text in enumerate(texts):
        thread = threading.Thread(target=translate_worker, args=(text, from_lang_code, to_lang_code, translations, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return translations

def take_screenshot():
    root = tk.Tk()
    root.withdraw()

    def on_mouse_down(event):
        global rect, start_x, start_y
        start_x, start_y = event.x, event.y
        rect = canvas.create_rectangle(start_x, start_y, start_x, start_y, outline='red')

    def on_mouse_drag(event):
        canvas.coords(rect, start_x, start_y, event.x, event.y)

    def on_mouse_up(event):
        selection_root.withdraw()
        img = pyautogui.screenshot(region=(
            min(start_x, event.x), min(start_y, event.y),
            abs(event.x - start_x), abs(event.y - start_y)
        ))
        queue.put(img)
        selection_root.destroy()

    selection_root = Toplevel(root)
    selection_root.title("截图")
    selection_root.attributes("-fullscreen", True)
    selection_root.attributes("-alpha", 0.3)
    selection_root.overrideredirect(1)
    selection_root.attributes("-topmost", True)

    canvas = tk.Canvas(selection_root, cursor="cross")
    canvas.pack(fill="both", expand=True)

    canvas.bind("<Button-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_drag)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)

    selection_root.mainloop()
    root.destroy()

def display_options_from_queue():
    while not queue.empty():
        img = queue.get()
        threading.Thread(target=show_options, args=(img,), daemon=True).start()
    root.after(100, display_options_from_queue)

def show_options(img):
    options_root = Toplevel(root)
    options_root.title("截图选项")

    img_display = ImageTk.PhotoImage(img)
    img_label = tk.Label(options_root, image=img_display)
    img_label.image = img_display
    img_label.pack(pady=(5, 10))

    LANGUAGES = {
        '中文': 'zh',
        '英语': 'en',
    }

    from_lang_var = tk.StringVar(value='英语')
    to_lang_var = tk.StringVar(value='中文')

    lang_frame = tk.Frame(options_root)
    lang_frame.pack(pady=(5, 10))

    from_label = tk.Label(lang_frame, textvariable=from_lang_var)
    to_label = tk.Label(lang_frame, textvariable=to_lang_var)

    def swap_languages():
        from_lang_var.set('中文' if from_lang_var.get() == '英语' else '英语')
        to_lang_var.set('中文' if to_lang_var.get() == '英语' else '英语')

    arrow_button = tk.Button(lang_frame, text='↔', command=swap_languages)

    from_label.grid(row=0, column=0, padx=5)
    arrow_button.grid(row=0, column=1, padx=5)
    to_label.grid(row=0, column=2, padx=5)

    def retake():
        options_root.destroy()
        threading.Thread(target=take_screenshot, daemon=True).start()

    async def extract_text():
        try:
            preprocessed_img = preprocess_image(img)
            text = await asyncio.to_thread(cached_ocr, preprocessed_img, 'chi_sim+chi_tra+eng')
            show_text_window(text, "提取的文字", options_root.winfo_width())
        except Exception as e:
            show_text_window(f"Error extracting text: {e}", "错误", options_root.winfo_width())

    async def translate():
        try:
            from_lang_code = LANGUAGES[from_lang_var.get()]
            to_lang_code = LANGUAGES[to_lang_var.get()]

            preprocessed_img = preprocess_image(img)
            text = await asyncio.to_thread(cached_ocr, preprocessed_img, 'chi_sim+chi_tra+eng')
            
            texts = text.split('\n')
            translated_texts = translate_in_parallel(texts, from_lang_code, to_lang_code)
            translated_text = '\n'.join(translated_texts)
            
            show_text_window(translated_text, "翻译结果", options_root.winfo_width())
        except Exception as e:
            show_text_window(f"Error translating text: {e}", "错误", options_root.winfo_width())

    def show_text_window(text, title, parent_width):
        text_window = Toplevel(root)
        text_window.title(title)
        
        text_window.geometry(f"{parent_width}x200")

        text_area = tk.Text(text_window, wrap="word")
        text_area.pack(expand=True, fill="both")
        text_area.insert("1.0", text)

        def copy_and_close():
            root.clipboard_clear()
            root.clipboard_append(text)
            text_window.after(1, text_window.destroy)
            cancel()

        copy_button = tk.Button(text_window, text="复制到剪贴板", command=copy_and_close)
        copy_button.pack(pady=10)

    def save():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png", initialfile=str(uuid.uuid4())[:8],
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            img.save(file_path)
            print(f"Image saved to {file_path}.")

    def cancel():
        options_root.destroy()

    button_frame = tk.Frame(options_root)
    button_frame.pack(pady=(5, 10))

    for text, command in [("重新截取", retake), 
                          ("提取文字", lambda: asyncio.run(extract_text())), 
                          ("翻译", lambda: asyncio.run(translate())), 
                          ("保存", save), ("取消", cancel)]:
        button = tk.Button(button_frame, text=text, command=command)
        button.pack(side="left", padx=5)

    options_root.update_idletasks()
    width = options_root.winfo_width()
    height = options_root.winfo_height()
    x = (options_root.winfo_screenwidth() // 2) - (width // 2)
    y = (options_root.winfo_screenheight() // 2) - (height // 2)
    options_root.geometry(f"+{x}+{y}")

def listen_for_screenshot():
    keyboard.add_hotkey('ctrl+alt+w', lambda: threading.Thread(target=take_screenshot, daemon=True).start())

queue = queue.Queue()

root = tk.Tk()
root.withdraw()

executor.submit(initialize_libraries)

root.after(100, display_options_from_queue)
threading.Thread(target=listen_for_screenshot, daemon=True).start()

root.mainloop()
