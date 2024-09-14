import tkinter as tk
from tkinter import Toplevel, filedialog, ttk
from PIL import Image, ImageTk
import uuid
import pyautogui
import pytesseract
import argostranslate.translate
import keyboard
import asyncio
import threading
import concurrent.futures
import queue

executor = concurrent.futures.ThreadPoolExecutor()

installed_languages = []

def initialize_libraries():
    global installed_languages
    try:
        installed_languages = argostranslate.translate.get_installed_languages()
        pytesseract.image_to_string(Image.new('RGB', (10, 10)))
    except Exception as e:
        print(f"Initialization error: {e}")

async def translate_text(text, from_lang_code, to_lang_code):
    try:
        def get_language(lang_code):
            return next((lang for lang in installed_languages if lang.code == lang_code), None)

        from_lang = get_language(from_lang_code)
        to_lang = get_language(to_lang_code)

        if not from_lang or not to_lang:
            return "Translation failed: Language package not found."

        if from_lang_code == 'zh' and to_lang_code != 'en':
            text = from_lang.get_translation(get_language('en')).translate(text)
            from_lang_code = 'en'
        
        elif from_lang_code != 'en' and to_lang_code == 'zh':
            text = from_lang.get_translation(get_language('en')).translate(text)
            from_lang_code = 'en'

        translated_text = from_lang.get_translation(to_lang).translate(text)
        return translated_text
    except Exception as e:
        return f"Translation error: {e}"

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
        img = pyautogui.screenshot(region=(min(start_x, event.x), min(start_y, event.y), abs(event.x - start_x), abs(event.y - start_y)))
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
        '日语': 'ja',
        '俄语': 'ru',
        '西班牙语': 'es',
        '德语': 'de',
        '法语': 'fr',
        '阿拉伯语': 'ar',
    }

    from_lang_var = tk.StringVar(value='英语')
    to_lang_var = tk.StringVar(value='中文')

    from_lang_menu = ttk.Combobox(options_root, textvariable=from_lang_var, values=list(LANGUAGES.keys()))
    to_lang_menu = ttk.Combobox(options_root, textvariable=to_lang_var, values=list(LANGUAGES.keys()))

    from_lang_menu.pack(pady=(5, 10))
    to_lang_menu.pack(pady=(5, 10))

    def retake():
        options_root.destroy()
        threading.Thread(target=take_screenshot, daemon=True).start()

    async def extract_text():
        try:
            text = await asyncio.to_thread(pytesseract.image_to_string, img, 'chi_sim+eng+spa+deu+fra+rus+ara+jpn')
            show_text_window(text, "提取的文字")
        except Exception as e:
            show_text_window(f"Error extracting text: {e}", "错误")

    async def translate():
        try:
            text = await asyncio.to_thread(pytesseract.image_to_string, img, 'eng')
            from_lang_code = LANGUAGES[from_lang_var.get()]
            to_lang_code = LANGUAGES[to_lang_var.get()]
            translated_text = await translate_text(text, from_lang_code, to_lang_code)
            show_text_window(translated_text, "翻译结果")
        except Exception as e:
            show_text_window(f"Error translating text: {e}", "错误")

    def show_text_window(text, title):
        text_window = Toplevel(root)
        text_window.title(title)
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
        file_path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=str(uuid.uuid4())[:8], filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
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
    keyboard.add_hotkey('ctrl+alt+s', lambda: threading.Thread(target=take_screenshot, daemon=True).start())
    keyboard.wait('esc')

queue = queue.Queue()

root = tk.Tk()
root.withdraw()

executor.submit(initialize_libraries)

root.after(100, display_options_from_queue)
threading.Thread(target=listen_for_screenshot, daemon=True).start()

root.mainloop()
