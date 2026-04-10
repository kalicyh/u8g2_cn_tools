# u8g2_cn_tools

适合 [u8g2](https://github.com/olikraus/u8g2) 的中文字体生成工具

## CLI

现在支持命令行直接输出项目可用的 `.u8f` 文件。

安装后可执行：

```bash
poetry run u8g2-cn-tools \
  --repo-root /path/to/Momentum-Firmware-CN \
  --strings localization/zh_CN/strings.json \
  --tools-dir /path/to/u8g2_cn_tools \
  --bdf /path/to/u8g2_cn_tools/bdf/fusion-pixel-10px-proportional-zh_hans.bdf \
  --work-dir /tmp/zh_fonts_work \
  --out-u8f /tmp/zh_fonts/primary_zh.u8f \
  --out-map /tmp/zh_fonts_work/primary_zh.map \
  --out-chars /tmp/zh_fonts_work/primary_zh_chars.txt \
  --font-name primary_zh
```

默认会扫描：

- `applications/main`
- `applications/services`
- `applications/settings`
- `lib`
- `assets/dolphin/**/meta.txt`

并合并 `strings.json` 的文本，最终生成：

- `.u8f`
- `.map`
- `chars.txt`

这样可以直接产出当前 Momentum Firmware CN 项目使用的字体格式。

## 界面

![QQ20240917-145610](https://github.com/user-attachments/assets/313c1784-edb0-4a36-bf6d-8f62cdf69183)

![QQ20240917-150057](https://github.com/user-attachments/assets/52ac11a0-e38b-4e45-971a-4bde9a0a4b4e)

## 功能

- 支持文件导入过滤出中文
- 支持文件拖入
- 添加字体选择
- 支持选择文件夹
- 支持文件夹遍历 + 进度显示
- 增加自定义处理文件的格式
- 增加去除数组数字的复选框
- 增加添加`static`的复选框

## 自行编译 bdfconv

克隆`https://github.com/olikraus/u8g2`

```bash
cd tools/font/bdfconv
make
```

## 参考

- [larryli/u8g2_wqy](https://github.com/larryli/u8g2_wqy)

### 字体来源

- https://github.com/TakWolf/fusion-pixel-font
- https://github.com/Angelic47/FontChinese7x7
- https://github.com/SolidZORO/zpix-pixel-font
- http://wenq.org/


## 使用参考flipper zero的fap程序为例

```C
static const uint8_t kalicyh[1535] =
    //你的字
    ;

static void app_draw_callback(Canvas* canvas, void* ctx) {
    UNUSED(ctx);

    canvas_clear(canvas);
    canvas_set_custom_u8g2_font(canvas, kalicyh);

    char draw_str[44] = {};

    canvas_draw_str_aligned(canvas, 128, 2, AlignRight, AlignTop, "关于");
}
```
