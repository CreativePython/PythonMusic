# Toggle

Create a toggle button that switches on and off with each click.

Toggles are drawn between a starting point (x1, y1) and an ending point (x2, y2).

## Creating a Toggle

You can create a Toggle using the following functions:

```python
Toggle(x1, y1, x2, y2)
```

```python
Toggle(x1, y1, x2, y2, action, foregroundColor, backgroundColor, outlineColor, thickness, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x1` | `int or float` | _required_ | The horizontal position of the top-left corner, in pixels. |
| `y1` | `int or float` | _required_ | The vertical position of the top-left corner, in pixels. |
| `x2` | `int or float` | _required_ | The horizontal position of the bottom-right corner, in pixels. |
| `y2` | `int or float` | _required_ | The vertical position of the bottom-right corner, in pixels. |
| `action` | `function` | `None` | The function to call when the toggle changes; it receives the new value. |
| `foregroundColor` | `Color` | `Color.RED` | The color when on. |
| `backgroundColor` | `Color` | `Color.BLACK` | The color behind the toggle. |
| `outlineColor` | `Color` | `Color.CLEAR` | The outline color. |
| `thickness` | `int` | `3` | The outline thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the toggle, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the toggle is, from 0 (invisible) to 100 (fully visible). |

For example,

```python title="simpleToggle.py"
--8<-- "examples/_snippets/simpleToggle.py"
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a Toggle has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getValue()`](getValue.md) | Report whether the toggle is currently pressed. |
| [`setValue(newValue)`](setValue.md) | Set whether the toggle is pressed. |
| [`getColor()`](../../common/color/getColor.md) | Return the fader's foreground color. |
| [`setColor()`](../../common/color/setColor.md) | Set the fader's foreground color. |
| [`getForegroundColor()`](getForegroundColor.md) | Same as getColor(). |
| [`setForegroundColor()`](setForegroundColor.md) | Same as setColor(). |
| [`getBackgroundColor()`](getBackgroundColor.md) | Return the fader's background color. |
| [`setBackgroundColor()`](setBackgroundColor.md) | Set the fader's background color. |
| [`getOutlineColor()`](getOutlineColor.md) | Return the fader's outline color. |
| [`setOutlineColor()`](setOutlineColor.md) | Set the fader's outline color. |
| [`onAction()`](onAction.md) | Register a function to call when the toggle changes. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
