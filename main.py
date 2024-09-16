import os
import codecs
import re
import subprocess
import tkinter as tk
from tkinter import scrolledtext, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD

# 确保 temp 文件夹存在
temp_dir = 'temp'
os.makedirs(temp_dir, exist_ok=True)

# BDF 文件夹路径
bdf_dir = 'bdf'

def extract_chinese(text):
    # 提取文本中的所有中文字符
    pattern = re.compile(r'[\u4e00-\u9fff]')
    chinese_text = ''.join(pattern.findall(text))
    return chinese_text

def filter_comments(content):
    # 去除单行注释 (//)
    content = re.sub(r'//.*', '', content)

    # 去除多行注释 (/* ... */)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    return content

def process_file(input_file, output_file):
    # 打开输入文件
    with codecs.open(input_file, 'r', 'utf-8') as f:
        content = f.read()

    # 转换编码为c99的格式（模拟）
    content = content.encode('unicode_escape').decode('utf-8')

    # 查找并格式化符合要求的unicode字符
    pattern = re.compile(r'\\u([0-9a-fA-F]{4})')
    formatted_content = pattern.sub(r'$\1,\n', content)

    # 去重并排序
    unique_lines = sorted(set(formatted_content.splitlines()))

    # 过滤空行并将小写字母转为大写
    final_content = [line.upper() for line in unique_lines if line.strip()]

    # 写入输出文件
    header = '32-128,\n'
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        if final_content:
            # 写入首行
            f.write(header)
            # 写入每一行，并确保最后没有多余的换行符
            f.write('\n'.join(final_content))

def filter_comments_and_modify_c_content(c_content):
    # 去除单行注释 (//)
    c_content = re.sub(r'//.*', '', c_content)

    # 去除多行注释 (/* ... */)
    c_content = re.sub(r'/\*.*?\*/', '', c_content, flags=re.DOTALL)

    # 去除多余的空行
    c_content = "\n".join([line for line in c_content.splitlines() if line.strip()])

    # 删除 U8G2_FONT_SECTION("kalicyh")
    c_content = re.sub(r' U8G2_FONT_SECTION\("kalicyh"\)', '', c_content)

    # 在 const 前面添加 static
    c_content = re.sub(r'(?<!static\s)const', r'static const', c_content)

    return c_content

def run_bdfconv(output_text):
    # 获取选择的 BDF 文件名
    bdf_file = bdf_file_menu.get()
    if not bdf_file:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, "Please select a BDF file.")
        return

    # 定义命令参数
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
        # 运行命令但不显示日志
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # 读取生成的.c文件的内容
        with open(os.path.join(temp_dir, '_kalicyh_u8g2.c'), 'r', encoding='utf-8') as f:
            c_content = f.read()
        
        # 过滤掉.c文件中的注释、U8G2_FONT_SECTION("kalicyh") 并在 const 前面添加 static
        modified_content = filter_comments_and_modify_c_content(c_content)

        # 显示修改后的内容
        output_text.delete(1.0, tk.END)  # 清空输出框
        output_text.insert(tk.END, modified_content)  # 显示修改后的 .c 文件内容
    except subprocess.CalledProcessError as e:
        output_text.delete(1.0, tk.END)  # 清空输出框
        output_text.insert(tk.END, "Error occurred while running the command:\n" + e.stderr)

def on_convert_click(input_text, output_text):
    # 获取输入框中的内容，保存为文件
    input_file = os.path.join(temp_dir, 'gb.txt')
    output_file = os.path.join(temp_dir, 'gb.map')
    # 获取文本框内容并去掉结尾的换行符
    text_content = input_text.get(1.0, tk.END).strip()
    with open(input_file, 'w', encoding='utf-8', newline='') as f:
        f.write(text_content)
    
    # 处理文件
    process_file(input_file, output_file)
    
    # 运行bdfconv并显示.c文件内容
    run_bdfconv(output_text)

def choose_file(input_text):
    # 选择文件并提取中文内容
    file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
    if file_path:
        with codecs.open(file_path, 'r', 'utf-8') as f:
            content = f.read()

        # 过滤掉注释内容
        content_without_comments = filter_comments(content)

        # 提取中文并显示在输入框中
        chinese_content = extract_chinese(content_without_comments)
        input_text.delete(1.0, tk.END)  # 清空输入框
        input_text.insert(tk.END, chinese_content)  # 显示提取的中文

def copy_output(output_text):
    # 将输出框的内容复制到剪贴板
    output_content = output_text.get(1.0, tk.END).strip()
    root.clipboard_clear()  # 清空剪贴板
    root.clipboard_append(output_content)  # 将内容复制到剪贴板

def on_drop(event):
    # 获取拖放的文件路径
    file_path = event.data
    if file_path:
        file_path = file_path.replace('{', '').replace('}', '')  # 清理路径中的花括号
        if os.path.isfile(file_path):
            with codecs.open(file_path, 'r', 'utf-8') as f:
                content = f.read()

            # 过滤掉注释内容
            content_without_comments = filter_comments(content)

            # 提取中文并显示在输入框中
            chinese_content = extract_chinese(content_without_comments)
            input_text.delete(1.0, tk.END)  # 清空输入框
            input_text.insert(tk.END, chinese_content)  # 显示提取的中文

def update_bdf_files():
    bdf_files = [f for f in os.listdir(bdf_dir) if f.endswith('.bdf')]
    menu = bdf_file_dropdown['menu']
    menu.delete(0, 'end')  # Clear existing options
    for bdf_file in bdf_files:
        menu.add_command(label=bdf_file, command=tk._setit(bdf_file_menu, bdf_file))

# 创建主窗口
root = TkinterDnD.Tk()  # 使用 TkinterDnD 的 Tk 类
root.title("Unicode转换工具")

# 创建输入文本框
input_label = tk.Label(root, text="输入文本/选择文件/拖入文件:")
input_label.pack()
input_text = scrolledtext.ScrolledText(root, height=10)
input_text.pack()

# 注册拖放功能
input_text.drop_target_register(DND_FILES)
input_text.dnd_bind('<<Drop>>', on_drop)

# 创建选择文件按钮
choose_file_button = tk.Button(root, text="选择文件", command=lambda: choose_file(input_text))
choose_file_button.pack()

# 创建下拉选择框
bdf_frame = tk.Frame(root)
bdf_frame.pack(fill=tk.X, padx=10, pady=5)

bdf_file_label = tk.Label(bdf_frame, text="选择BDF文件:")
bdf_file_label.pack(side=tk.LEFT)
bdf_file_menu = tk.StringVar(root)
bdf_file_menu.set("fusion-pixel-10px-proportional-zh_hans.bdf")
bdf_file_dropdown = tk.OptionMenu(bdf_frame, bdf_file_menu, [])
bdf_file_dropdown.pack(side=tk.LEFT)

# 更新 BDF 文件列表
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

# 启动GUI主循环
root.mainloop()
