import os
import codecs
import re
import subprocess
import tkinter as tk
from tkinter import scrolledtext, filedialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import chardet

# 确保 temp 文件夹存在
temp_dir = 'temp'
os.makedirs(temp_dir, exist_ok=True)

# BDF 文件夹路径
bdf_dir = 'bdf'

def extract_chinese(text):
    pattern = re.compile(r'[\u4e00-\u9fff]')
    chinese_text = ''.join(pattern.findall(text))
    return chinese_text

def filter_comments(content):
    content = re.sub(r'//.*', '', content)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    return content

def process_file(input_file, output_file):
    with codecs.open(input_file, 'r', 'utf-8') as f:
        content = f.read()
    content = content.encode('unicode_escape').decode('utf-8')
    pattern = re.compile(r'\\u([0-9a-fA-F]{4})')
    formatted_content = pattern.sub(r'$\1,\n', content)
    unique_lines = sorted(set(formatted_content.splitlines()))
    final_content = [line.upper() for line in unique_lines if line.strip()]
    header = '32-128,\n'
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        if final_content:
            f.write(header)
            f.write('\n'.join(final_content))

def filter_comments_and_modify_c_content(c_content):
    c_content = re.sub(r'//.*', '', c_content)
    c_content = re.sub(r'/\*.*?\*/', '', c_content, flags=re.DOTALL)
    c_content = "\n".join([line for line in c_content.splitlines() if line.strip()])
    c_content = re.sub(r' U8G2_FONT_SECTION\("kalicyh"\)', '', c_content)
    c_content = re.sub(r'(?<!static\s)const', r'static const', c_content)
    return c_content

def run_bdfconv(output_text):
    bdf_file = bdf_file_menu.get()
    if not bdf_file:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, "Please select a BDF file.")
        return
    cmd = [
        './bdfconv',
        os.path.join(bdf_dir, bdf_file),
        '-b', '0',
        '-f', '1',
        '-M', os.path.join(temp_dir, 'gb.map'),
        '-n', 'kalicyh',
        '-o', os.path.join(temp_dir, '_kalicyh_u8g2.c')
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        with open(os.path.join(temp_dir, '_kalicyh_u8g2.c'), 'r', encoding='utf-8') as f:
            c_content = f.read()
        modified_content = filter_comments_and_modify_c_content(c_content)
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, modified_content)
    except subprocess.CalledProcessError as e:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, "Error occurred while running the command:\n" + e.stderr)

def on_convert_click(input_text, output_text):
    input_file = os.path.join(temp_dir, 'gb.txt')
    output_file = os.path.join(temp_dir, 'gb.map')
    text_content = input_text.get(1.0, tk.END).strip()
    with open(input_file, 'w', encoding='utf-8', newline='') as f:
        f.write(text_content)
    process_file(input_file, output_file)
    run_bdfconv(output_text)

def choose_file(input_text):
    file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
    if file_path:
        with codecs.open(file_path, 'r', 'utf-8') as f:
            content = f.read()
        content_without_comments = filter_comments(content)
        chinese_content = extract_chinese(content_without_comments)
        input_text.delete(1.0, tk.END)
        input_text.insert(tk.END, chinese_content)

def choose_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        # 更新进度条
        progress['value'] = 0
        root.update_idletasks()

        # 获取文件总数
        file_count = sum([len(files) for r, d, files in os.walk(folder_path) if any(file.lower().endswith(('.c', '.h')) for file in files)])
        processed_count = 0

        # 使用 os.walk() 递归遍历文件夹
        for root_dir, dirs, files in os.walk(folder_path):
            for file_name in files:
                # 仅处理 .c 和 .h 文件
                if file_name.lower().endswith(('.c', '.h')):
                    file_path = os.path.join(root_dir, file_name)
                    
                    if os.path.isfile(file_path):  # 确保只处理文件
                        try:
                            # 自动检测文件编码
                            with open(file_path, 'rb') as f:
                                raw_data = f.read()
                            result = chardet.detect(raw_data)
                            encoding = result['encoding']

                            # 使用检测到的编码读取文件内容
                            with codecs.open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                                content = f.read()
                            
                            # 过滤注释并提取中文内容
                            content_without_comments = filter_comments(content)
                            chinese_content = extract_chinese(content_without_comments)

                            # 在输入文本框中插入提取到的中文内容
                            input_text.insert(tk.END, f'{chinese_content}')

                            # 保存提取的中文内容到临时文件
                            input_file = os.path.join(temp_dir, 'gb.txt')
                            with open(input_file, 'w', encoding='utf-8', newline='') as f:
                                f.write(chinese_content)

                            # 处理文件并生成输出内容
                            output_file = os.path.join(temp_dir, 'gb.map')
                            process_file(input_file, output_file)

                            # 更新进度条
                            processed_count += 1
                            progress['value'] = (processed_count / file_count) * 100
                            root.update_idletasks()

                        except Exception as e:
                            # 错误处理
                            print(f"Error processing file {file_path}: {e}")

        # 完成后将进度条设置为100%
        progress['value'] = 100
        root.update_idletasks()

def copy_output(output_text):
    output_content = output_text.get(1.0, tk.END).strip()
    root.clipboard_clear()
    root.clipboard_append(output_content)

def on_drop(event):
    file_path = event.data
    if file_path:
        file_path = file_path.replace('{', '').replace('}', '')
        if os.path.isfile(file_path):
            with codecs.open(file_path, 'r', 'utf-8') as f:
                content = f.read()
            content_without_comments = filter_comments(content)
            chinese_content = extract_chinese(content_without_comments)
            input_text.delete(1.0, tk.END)
            input_text.insert(tk.END, chinese_content)

def update_bdf_files():
    bdf_files = [f for f in os.listdir(bdf_dir) if f.endswith('.bdf')]
    menu = bdf_file_dropdown['menu']
    menu.delete(0, 'end')
    for bdf_file in bdf_files:
        menu.add_command(label=bdf_file, command=tk._setit(bdf_file_menu, bdf_file))

def remove_duplicates():
    text_content = input_text.get(1.0, tk.END).strip()
    unique_content = ''.join(sorted(set(text_content), key=text_content.index))
    input_text.delete(1.0, tk.END)
    input_text.insert(tk.END, unique_content)

# 创建主窗口
root = TkinterDnD.Tk()
root.title("Unicode转换工具")

# 创建输入文本框
input_label = tk.Label(root, text="输入文本/选择文件/拖入文件:")
input_label.pack()
input_text = scrolledtext.ScrolledText(root, height=10)
input_text.pack()

# 注册拖放功能
input_text.drop_target_register(DND_FILES)
input_text.dnd_bind('<<Drop>>', on_drop)

# 创建按钮容器 Frame
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# 创建选择文件按钮
choose_file_button = tk.Button(button_frame, text="选择文件", command=lambda: choose_file(input_text))
choose_file_button.pack(side=tk.LEFT, padx=5)

# 创建选择文件夹按钮
choose_folder_button = tk.Button(button_frame, text="选择文件夹", command=choose_folder)
choose_folder_button.pack(side=tk.LEFT, padx=5)

# 创建去重按钮
remove_duplicates_button = tk.Button(button_frame, text="去重", command=remove_duplicates)
remove_duplicates_button.pack(side=tk.LEFT, padx=5)

# 创建下拉选择框
bdf_frame = tk.Frame(root)
bdf_frame.pack(fill=tk.X, padx=10, pady=5)

bdf_file_label = tk.Label(bdf_frame, text="选择BDF文件:")
bdf_file_label.pack(side=tk.LEFT)
bdf_file_menu = tk.StringVar(root)
bdf_file_menu.set("fusion-pixel-10px-proportional-zh_hans.bdf")
bdf_file_dropdown = tk.OptionMenu(bdf_frame, bdf_file_menu, [])
bdf_file_dropdown.pack(side=tk.LEFT)

update_bdf_files()

# 创建输出文本框
output_label = tk.Label(root, text="输出文件内容 (.c):")
output_label.pack()
output_text = scrolledtext.ScrolledText(root, height=20)
output_text.pack()

# 创建一个 Frame 容器来并排放置按钮
button_frame = tk.Frame(root)
button_frame.pack()

# 创建转换按钮
convert_button = tk.Button(button_frame, text="转换", command=lambda: on_convert_click(input_text, output_text))
convert_button.pack(side=tk.LEFT, padx=10)

# 创建复制按钮
copy_button = tk.Button(button_frame, text="复制", command=lambda: copy_output(output_text))
copy_button.pack(side=tk.LEFT, padx=10)

# 创建进度条
progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress.pack(pady=10)

# 启动GUI主循环
root.mainloop()
