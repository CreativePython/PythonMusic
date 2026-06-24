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
| `action` | `function` | `None` | The function to call when the checkbox changes; it receives one parameter, True if it was just checked or False if it was just unchecked. |
| `color` | `Color` | `Color.CLEAR` | The checkbox color. |

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
| [`setColor(color)`](setColor.md) | Set the checkbox's color. |

If you create a CheckBox without a callback function, it is a passive GUI element.  You can still check whether the CheckBox is checked or unchecked using these functions:

| Function | Description |
|---|---|
| [`check()`](check.md) | Check the checkbox. |
| [`uncheck()`](uncheck.md) | Uncheck the checkbox. |
| [`isChecked()`](isChecked.md) | Report whether the checkbox is checked. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
