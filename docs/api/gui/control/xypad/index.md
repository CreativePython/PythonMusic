# XYPad

An XYPad is similar to a trackpad. It is controlled by clicking and dragging a selector (tracker bubble) across the pad.

XYPads are drawn between a starting point (x1, y1) and an ending point (x2, y2).  Its value is an (x, y) position within the pad.

## Creating an XYPad

You can create an XYPad using the following functions:

```python
xypad = XYPad(x1, y1, x2, y2)
```

```python
XYPad(x1, y1, x2, y2, action, foregroundColor, backgroundColor, outlineColor, outlineThickness, trackerRadius, crosshairThickness, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x1` | `int or float` | _required_ | The horizontal position of the top-left corner, in pixels. |
| `y1` | `int or float` | _required_ | The vertical position of the top-left corner, in pixels. |
| `x2` | `int or float` | _required_ | The horizontal position of the bottom-right corner, in pixels. |
| `y2` | `int or float` | _required_ | The vertical position of the bottom-right corner, in pixels. |
| `action` | `function` | `None` | The function to call when the tracker moves; it receives the new [x, y] value. |
| `foregroundColor` | `Color` | `Color.RED` | The color of the tracker. |
| `backgroundColor` | `Color` | `Color.BLACK` | The color behind the tracker. |
| `outlineColor` | `Color` | `Color.CLEAR` | The outline color. |
| `outlineThickness` | `int` | `2` | The outline thickness, in pixels. |
| `trackerRadius` | `int or float` | `10` | The radius of the tracker, in pixels. |
| `crosshairThickness` | `int` | `None` | The thickness of the crosshair lines, in pixels. Defaults to the outline thickness. |
| `rotation` | `int or float` | `0` | How far to turn the pad, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the pad is, from 0 (invisible) to 100 (fully visible). |

For example,

```python title="simpleXYPad.py"
--8<-- "examples/_snippets/simpleXYPad.py"
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once an XYPad has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getValue()`](getValue.md) | Return the tracker's position within the pad. |
| [`setValue(x, y)`](setValue.md) | Set the tracker's position within the pad. |
| [`getForegroundColor()`](getForegroundColor.md) | Return the xypad's foreground color. |
| [`setForegroundColor()`](setForegroundColor.md) | Set the xypad's foreground color. |
| [`getBackgroundColor()`](getBackgroundColor.md) | Return the xypad's background color. |
| [`setBackgroundColor()`](setBackgroundColor.md) | Set the xypad's background color. |
| [`getOutlineColor()`](getOutlineColor.md) | Return the xypad's outline color. |
| [`setOutlineColor()`](setOutlineColor.md) | Set the xypad's outline color. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Color](../../common/index.md#color-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
