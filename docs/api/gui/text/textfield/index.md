# TextField

Create a single-line text field the user can type into.

If you create a TextField with a callback function, then that function will be called anytime the enter key is typed inside the box. (Presumably, the user will change the text and then press enter.)

## Creating a TextField

You can create a TextField using the following functions:

```python
TextField()
```

```python
TextField(text, columns, action, color, font)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `str` | `''` | The text to start with. |
| `columns` | `int` | `8` | The width of the field, in characters. |
| `action` | `function` | `None` | The function to call when the user presses Enter in the field; it receives one parameter, the field's contents as a string. |
| `color` | `Color` | `Color.WHITE` | The field color. |
| `font` | `Font` | `None` | The font, for example `Font("Serif", Font.ITALIC, 16)`. If omitted, the default font is used. |

For example,

```python
textfield = TextField("type and hit <ENTER> ", 18, processEntry)
```

where `processEntry` is a function which expects one parameter, the updated text (a string).

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a TextField has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getText()`](getText.md) | Return the text in the field. |
| [`setText(text)`](setText.md) | Set the text in the field. |
| [`getColor()`](../../common/color/getColor.md) | Return the field's background color. |
| [`setColor(color)`](../../common/color/setColor.md) | Set the field's background color. |
| [`getFont()`](getFont.md) | Return the field's font. |
| [`setFont(font)`](setFont.md) | Set the field's font. |
| [`onAction(action)`](onAction.md) | Register a function to call when the user presses Enter in the field. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)


