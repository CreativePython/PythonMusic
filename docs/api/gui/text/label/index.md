# Label

Create a label that shows a line of text.

## Creating a Label

You can create a Label using the following functions:

```python
Label(text)
```

```python
Label(text, alignment, textColor, backgroundColor, font, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `str` | _required_ | The text to show. |
| `alignment` | `int` | `LEFT` | How the text lines up, one of `LEFT`, `CENTER`, or `RIGHT`. |
| `textColor` | `Color` | `Color.BLACK` | The text color. |
| `backgroundColor` | `Color` | `Color.CLEAR` | The color behind the text. Defaults to transparent. |
| `font` | `Font` | `None` | The font, for example `Font("Serif", Font.ITALIC, 16)`. If omitted, the system default font is used. |
| `visibility` | `int` | `100` | How visible the label is, from 0 (invisible) to 100 (fully visible). |

For example,

```python
label = Label("Hello World!")
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a Label has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getText()`](getText.md) | Return the label's text. |
| [`setText(text)`](setText.md) | Set the label's text. |
| [`getAlignment()`](getAlignment.md) | Return how the label's text lines up. |
| [`setAlignment(alignment)`](setAlignment.md) | Set how the label's text lines up. |
| [`getFont()`](getFont.md) | Return the label's font. |
| [`setFont(font)`](setFont.md) | Set the label's font. |
| [`getTextColor()`](getTextColor.md) | Return the label's text color. |
| [`setTextColor()`](setTextColor.md) | Set the label's text color. |
| [`getBackgroundColor()`](getBackgroundColor.md) | Return the label's background color. |
| [`setBackgroundColor()`](setBackgroundColor.md) | Set the label's background color. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Color](../../common/index.md#color-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
