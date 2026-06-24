# TextArea

Create a multi-line text area the user can type into.

TextArea objects are used for entering text that may span several lines.  If the text is taller than the area, a scroll bar appears on the right.

## Creating a TextArea

You can create a TextArea using the following functions:

```python
TextArea()
```

```python
TextArea(text, columns, rows, color, font)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `str` | `''` | The text to start with. |
| `columns` | `int` | `8` | The width of the area, in characters. |
| `rows` | `int` | `5` | The height of the area, in lines. |
| `color` | `Color` | `Color.WHITE` | The area's background color. |
| `font` | `Font` | `None` | The font, for example `Font("Serif", Font.ITALIC, 16)`. If omitted, the default font is used. |

For example,

```python
textarea = TextArea("Start Typing...", 10, 8, Color.YELLOW)
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a TextArea has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getText()`](getText.md) | Return the text in the area. |
| [`setText(text)`](setText.md) | Set the text in the area. |
| [`getColor()`](../common/color/getColor.md) | Return the area's background color. |
| [`setColor(color)`](../common/color/setColor.md) | Set the area's background color. |
| [`getFont()`](getFont.md) | Return the area's font. |
| [`setFont(font)`](setFont.md) | Set the area's font. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
