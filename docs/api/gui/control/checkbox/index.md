# CheckBox

Create a checkbox the user can check and uncheck.

## Creating a CheckBox

You can create a CheckBox using the following functions:

```python
CheckBox()
```

```python
CheckBox(text, action, color)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `str` | `''` | The text shown beside the checkbox. |
| `action` | `function` | `None` | The function to call when the checkbox changes; it receives one parameter, `True` if it was just checked or `False` if it was just unchecked. |
| `color` | `Color` | `Color.CLEAR` | The checkbox color. |
| `rotation` | `int or float` | `0` | How far to turn the checkbox, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the checkbox is, from 0 (invisible) to 100 (fully visible). |

For example,

```python
checkbox = Checkbox("Check Me Out!")
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a CheckBox has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getText()`](getText.md) | Return the checkbox's text. |
| [`setText(text)`](setText.md) | Set the checkbox's text. |
| [`getColor()`](../../common/color/getColor.md) | Return the checkbox's color. |
| [`setColor(color)`](../../common/color/setColor.md) | Set the checkbox's color. |
| [`check()`](check.md) | Check the checkbox. |
| [`uncheck()`](uncheck.md) | Uncheck the checkbox. |
| [`isChecked()`](isChecked.md) | Report whether the checkbox is checked. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
