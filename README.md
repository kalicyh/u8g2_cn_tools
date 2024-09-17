# u8g2_cn_tools

适合 [u8g2](https://github.com/olikraus/u8g2) 的中文字体生成工具

## 界面

![QQ20240916-185819](https://github.com/user-attachments/assets/fb163d9c-d997-44a9-a20e-d8e3ef3cbd8a)

## 功能

- 支持文件导入过滤出中文
- 支持文件拖入
- 添加字体选择
- 支持选择文件夹
- 支持文件夹遍历 + 进度显示

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
