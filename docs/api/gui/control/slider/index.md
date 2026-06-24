# Slider

Create a slider the user can drag to choose a value.

## Creating a Slider

You can create a Slider using the following functions:

```python
Slider()
```

```python
Slider(orientation, minValue, maxValue, startValue, action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `orientation` | `int` | `HORIZONTAL` | The slider direction, either `HORIZONTAL` or `VERTICAL`. |
| `minValue` | `int` | `0` | The smallest value the slider can take. |
| `maxValue` | `int` | `100` | The largest value the slider can take. |
| `startValue` | `int or float` | `None` | The slider's starting value. Defaults to halfway between `minValue` and `maxValue`. |
| `action` | `function` | `None` | The function to call when the slider moves; it receives one parameter, the new value. |
| `color` | `Color` | `Color.LIGHT_GRAY` | The slider's handle color. |
| `rotation` | `int or float` | `0` | How far to turn the slider, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the slider is, from 0 (invisible) to 100 (fully visible). |

For example,

```python
slider = Slider(VERTICAL, 0, 127, 50, changeVolume)
```

where `changeVolume` is a function which expects one parameter, the new value of the slider. When the function is called, it may use this value to update the volume of some musical material, for instance.

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a Slider has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getValue()`](getValue.md) | Return the slider's current value. |
| [`setValue(value)`](setValue.md) | Set the slider's value. |
| [`getColor()`](../../common/color/getColor.md) | Return the slider's handle color. |
| [`setColor(color)`](../../common/color/setColor.md) | Set the slider's handle color. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
