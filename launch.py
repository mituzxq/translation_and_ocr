import subprocess
import time

# 检查某个进程是否在运行
def is_process_running(process_name):
    with subprocess.Popen(
        ["tasklist", "/fi", f"imagename eq {process_name}"], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
        text=True, creationflags=subprocess.CREATE_NO_WINDOW
    ) as proc:
        result = proc.communicate()[0]
    return process_name in result

def start_application_if_not_running_no_window(process_name, shortcut_path):
    if not is_process_running(process_name):
        subprocess.Popen(shortcut_path)

# 无限循环，定期检查进程并尝试相关操作
while True:
    try:
        start_application_if_not_running_no_window(
            "ocr_and_Translation.exe",
            "C:\\path\\to\\your\\ocr_and_Translation.exe"   # 绝对路径
        )
    except Exception:
        pass
    time.sleep(10)  # 每隔 10 秒重复一次
