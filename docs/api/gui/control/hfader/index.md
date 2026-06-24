# HFader

Create a horizontal fader the user can drag left and right.

Faders are drawn between a starting point (x1, y1) and an ending point (x2, y2).

There are two types of faders, a horizontal fader (HFader) and a [vertical fader (VFader)](../vfader/index.md).

## Creating an HFader

You can create an HFader using the following functions:

```python
HFader(x1, y1, x2, y2)
```

```python
HFader(x1, y1, x2, y2, minValue, maxValue, startValue, action, foregroundColor, backgroundColor, outlineColor, thickness, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x1` | `int or float` | _required_ | The horizontal position of the top-left corner, in pixels. |
| `y1` | `int or float` | _required_ | The vertical position of the top-left corner, in pixels. |
| `x2` | `int or float` | _required_ | The horizontal position of the bottom-right corner, in pixels. |
| `y2` | `int or float` | _required_ | The vertical position of the bottom-right corner, in pixels. |
| `minValue` | `int` | `0` | The smallest value the fader can take. |
| `maxValue` | `int` | `999` | The largest value the fader can take. |
| `startValue` | `int or float` | `None` | The fader's starting value. Defaults to halfway between minValue and maxValue. |
| `action` | `function` | `None` | The function to call when the fader moves; it receives the new value. |
| `foregroundColor` | `Color` | `Color.RED` | The color of the filled level. |
| `backgroundColor` | `Color` | `Color.BLACK` | The color behind the level. |
| `outlineColor` | `Color` | `Color.BLACK` | The outline color. |
| `thickness` | `int` | `3` | The outline thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the fader, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the fader is, from 0 (invisible) to 100 (fully visible). |

For example, 

```python title="simpleFader.py"
--8<-- "examples/_snippets/simpleFader.py"
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once an HFader has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getValue()`](getValue.md) | Return the fader's current value. |
| [`setValue(newValue)`](setValue.md) | Set the fader's value. |
| [`onAction()`](onAction.md) | Register a function to call when the fader moves. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)