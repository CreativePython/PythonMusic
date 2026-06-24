# Rotary

Create a rotary knob the user can turn.

Rotaries are drawn between a starting point (x1, y1) and an ending point (x2, y2). Its lowest and highest values sit at the bottom, and it rotates around `arcWidth` degrees in between.

## Creating a Rotary

You can create a Rotary using the following functions:

```python
Rotary(x1, y1, x2, y2)
```

```python
Rotary(x1, y1, x2, y2, minValue, maxValue, startValue, action, foregroundColor, backgroundColor, outlineColor, thickness, arcWidth, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x1` | `int or float` | _required_ | The horizontal position of the top-left corner, in pixels. |
| `y1` | `int or float` | _required_ | The vertical position of the top-left corner, in pixels. |
| `x2` | `int or float` | _required_ | The horizontal position of the bottom-right corner, in pixels. |
| `y2` | `int or float` | _required_ | The vertical position of the bottom-right corner, in pixels. |
| `minValue` | `int` | `0` | The smallest value the knob can take. |
| `maxValue` | `int` | `999` | The largest value the knob can take. |
| `startValue` | `int or float` | `None` | The knob's starting value. Defaults to halfway between minValue and maxValue. |
| `action` | `function` | `None` | The function to call when the knob turns; it receives the new value. |
| `foregroundColor` | `Color` | `Color.RED` | The color of the level shown by the knob. |
| `backgroundColor` | `Color` | `Color.BLACK` | The color behind the knob. |
| `outlineColor` | `Color` | `Color.BLUE` | The outline color. |
| `thickness` | `int` | `3` | The outline thickness, in pixels. |
| `arcWidth` | `int or float` | `300` | How far the knob turns from lowest to highest, in degrees. A typical value is 300. |
| `rotation` | `int or float` | `0` | How far to turn the whole control, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the knob is, from 0 (invisible) to 100 (fully visible). |

For example,

```python title="simpleRotary.py"
--8<-- "examples/_snippets/simpleRotary.py"
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a Rotary has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getValue()`](getValue.md) | Return the rotary's current value. |
| [`setValue(newValue)`](setValue.md) | Set the rotary's value. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)