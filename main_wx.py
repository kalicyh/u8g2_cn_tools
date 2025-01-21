import os
import codecs
import re
import subprocess
import wx
import wx.lib.mixins.listctrl as listmix
from wx.lib.dialogs import ScrolledMessageDialog
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

    if add_static_var.GetValue():
        c_content = re.sub(r'(?<!static\s)const', r'static const', c_content)

    if remove_array_length_var.GetValue():
        c_content = re.sub(r'\[\d+\]', '[]', c_content)

    return c_content

def run_bdfconv(output_text):
    bdf_file = bdf_file_menu.GetValue()
    if not bdf_file:
        output_text.SetValue("Please select a BDF file.")
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
        output_text.SetValue(modified_content)
    except subprocess.CalledProcessError as e:
        output_text.SetValue("Error occurred while running the command:\n" + e.stderr)

def on_convert_click(input_text, output_text):
    input_file = os.path.join(temp_dir, 'gb.txt')
    output_file = os.path.join(temp_dir, 'gb.map')
    text_content = input_text.GetValue().strip()
    with open(input_file, 'w', encoding='utf-8', newline='') as f:
        f.write(text_content)
    process_file(input_file, output_file)
    run_bdfconv(output_text)

def choose_file(input_text):
    file_dialog = wx.FileDialog(None, "Open file", wildcard="All files (*.*)|*.*", style=wx.FD_OPEN)
    if file_dialog.ShowModal() == wx.ID_OK:
        file_path = file_dialog.GetPath()
        with codecs.open(file_path, 'r', 'utf-8') as f:
            content = f.read()
        content_without_comments = filter_comments(content)
        chinese_content = extract_chinese(content_without_comments)
        input_text.SetValue(chinese_content)

def choose_folder():
    folder_dialog = wx.DirDialog(None, "Choose a folder", style=wx.DD_DEFAULT_STYLE)
    if folder_dialog.ShowModal() == wx.ID_OK:
        folder_path = folder_dialog.GetPath()
        extensions = extension_entry.GetValue().strip().split(',')
        extensions = [ext.strip().lower() for ext in extensions]

        progress.SetValue(0)
        wx.Yield()

        file_count = sum([len(files) for r, d, files in os.walk(folder_path) if any(file.lower().endswith(tuple(extensions)) for file in files)])
        processed_count = 0

        for root_dir, dirs, files in os.walk(folder_path):
            for file_name in files:
                if file_name.lower().endswith(tuple(extensions)):
                    file_path = os.path.join(root_dir, file_name)

                    if os.path.isfile(file_path):
                        try:
                            with open(file_path, 'rb') as f:
                                raw_data = f.read()
                            result = chardet.detect(raw_data)
                            encoding = result['encoding']

                            with codecs.open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                                content = f.read()

                            content_without_comments = filter_comments(content)
                            chinese_content = extract_chinese(content_without_comments)

                            input_text.AppendText(f'{chinese_content}')

                            input_file = os.path.join(temp_dir, 'gb.txt')
                            with open(input_file, 'w', encoding='utf-8', newline='') as f:
                                f.write(chinese_content)

                            output_file = os.path.join(temp_dir, 'gb.map')
                            process_file(input_file, output_file)

                            processed_count += 1
                            progress.SetValue((processed_count / file_count) * 100)
                            wx.Yield()

                        except Exception as e:
                            print(f"Error processing file {file_path}: {e}")

        progress.SetValue(100)
        wx.Yield()

def copy_output(output_text):
    output_content = output_text.GetValue().strip()
    wx.TheClipboard.Open()
    wx.TheClipboard.SetData(wx.TextDataObject(output_content))
    wx.TheClipboard.Close()

def remove_duplicates():
    text_content = input_text.GetValue().strip()
    unique_content = ''.join(sorted(set(text_content), key=text_content.index))
    input_text.SetValue(unique_content)

def sort_text_by_unicode():
    text_content = input_text.GetValue().strip()
    sorted_content = ''.join(sorted(text_content))
    input_text.SetValue(sorted_content)

def update_bdf_files():
    bdf_files = [f for f in os.listdir(bdf_dir) if f.endswith('.bdf')]
    bdf_file_menu.Clear()
    for bdf_file in bdf_files:
        bdf_file_menu.Append(bdf_file)
    bdf_file_menu.SetValue(bdf_files[0])

# 创建 wxPython 应用
app = wx.App(False)

# 创建主窗口
frame = wx.Frame(None, title="Unicode转换工具", size=(800, 600))

# 创建面板
panel = wx.Panel(frame)

# 扩展名输入框
extension_label = wx.StaticText(panel, label="输入处理文件的后缀 (如：c,h,txt):")
extension_entry = wx.TextCtrl(panel, value="c,h", style=wx.TE_LEFT)

# 输入文本框
input_label = wx.StaticText(panel, label="输入文本/选择文件/拖入文件:")
input_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_AUTO_URL)

# 复选框
add_static_var = wx.CheckBox(panel, label="在开头添加 static")
remove_array_length_var = wx.CheckBox(panel, label="移除数组长度")

# 文件选择按钮
choose_file_button = wx.Button(panel, label="选择文件")
choose_folder_button = wx.Button(panel, label="选择文件夹")
remove_duplicates_button = wx.Button(panel, label="去重")
sort_button = wx.Button(panel, label="排序")

# BDF 文件选择
bdf_file_label = wx.StaticText(panel, label="选择BDF文件:")
bdf_file_menu = wx.ComboBox(panel, choices=[], style=wx.CB_DROPDOWN)
update_bdf_files()

# 输出文本框
output_label = wx.StaticText(panel, label="输出文件内容 (.c):")
output_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)

# 转换按钮
convert_button = wx.Button(panel, label="转换")
copy_button = wx.Button(panel, label="复制")

# 进度条
progress = wx.Gauge(panel, range=100, size=(300, 25))

# 布局
sizer = wx.BoxSizer(wx.VERTICAL)

sizer.Add(extension_label, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(extension_entry, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(input_label, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(input_text, 1, wx.EXPAND | wx.ALL, 5)
sizer.Add(add_static_var, 0, wx.ALL, 5)
sizer.Add(remove_array_length_var, 0, wx.ALL, 5)
sizer.Add(choose_file_button, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(choose_folder_button, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(remove_duplicates_button, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(sort_button, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(bdf_file_label, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(bdf_file_menu, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(output_label, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(output_text, 1, wx.EXPAND | wx.ALL, 5)
sizer.Add(convert_button, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(copy_button, 0, wx.EXPAND | wx.ALL, 5)
sizer.Add(progress, 0, wx.EXPAND | wx.ALL, 5)

panel.SetSizer(sizer)

# 事件绑定
choose_file_button.Bind(wx.EVT_BUTTON, lambda event: choose_file(input_text))
choose_folder_button.Bind(wx.EVT_BUTTON, choose_folder)
remove_duplicates_button.Bind(wx.EVT_BUTTON, remove_duplicates)
sort_button.Bind(wx.EVT_BUTTON, sort_text_by_unicode)
convert_button.Bind(wx.EVT_BUTTON, lambda event: on_convert_click(input_text, output_text))
copy_button.Bind(wx.EVT_BUTTON, lambda event: copy_output(output_text))

frame.Show()
app.MainLoop()
