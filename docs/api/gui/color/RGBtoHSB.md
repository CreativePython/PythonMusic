# RGBtoHSB()

Convert a color from RGB to HSB (hue, saturation, brightness).

## Parameters

`Color.RGBtoHSB()` is a static utility. Call it on the `Color` class itself, for example:

```python
Color.RGBtoHSB(red, green, blue)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `red` | `int` | _required_ | The red component, from 0 to 255. |
| `green` | `int` | _required_ | The green component, from 0 to 255. |
| `blue` | `int` | _required_ | The blue component, from 0 to 255. |

## Returns

`return hue, saturation, brightness`

| Value | Type | Description |
|---|---|---|
| hue | `float` | The hue, from 0.0 to 1.0. |
| saturation | `float` | The saturation, from 0.0 to 1.0. |
| brightness | `float` | The brightness, from 0.0 to 1.0. |
