# Push

Create a push-and-hold button.

Push buttons are drawn between a starting point (x1, y1) and an ending point (x2, y2).  The button is on (True) only while it is held down.

## Creating a Push

You can create a Push using the following functions:

```python
Push(x1, y1, x2, y2)
```

```python
Push(x1, y1, x2, y2, action, foregroundColor, backgroundColor, outlineColor, thickness, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x1` | `int or float` | _required_ | The horizontal position of the top-left corner, in pixels. |
| `y1` | `int or float` | _required_ | The vertical position of the top-left corner, in pixels. |
| `x2` | `int or float` | _required_ | The horizontal position of the bottom-right corner, in pixels. |
| `y2` | `int or float` | _required_ | The vertical position of the bottom-right corner, in pixels. |
| `action` | `function` | `None` | The function to call when the button is pressed or released; it receives the new value. |
| `foregroundColor` | `Color` | `Color.RED` | The color while pressed. |
| `backgroundColor` | `Color` | `Color.BLACK` | The color behind the button. |
| `outlineColor` | `Color` | `Color.CLEAR` | The outline color. |
| `thickness` | `int` | `3` | The outline thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the button, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the button is, from 0 (invisible) to 100 (fully visible). |

For example,

```python title="simplePush.py"
--8<-- "examples/_snippets/simplePush.py"
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a Push has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getValue()`](getValue.md) | Report whether the push button is currently held down. |
| [`setValue(newValue)`](setValue.md) | Set whether the push button is pressed. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
