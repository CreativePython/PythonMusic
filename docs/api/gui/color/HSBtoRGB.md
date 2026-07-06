# HSBtoRGB()

Convert a color from HSB (hue, saturation, brightness) to RGB.

Values outside 0.0 to 1.0 are clamped to that range.

## Parameters

`Color.HSBtoRGB()` is a static utility. Call it on the `Color` class itself, for example:

```python
Color.HSBtoRGB(hue, saturation, brightness)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hue` | `float` | _required_ | The hue, from 0.0 to 1.0. |
| `saturation` | `float` | _required_ | The saturation, from 0.0 to 1.0. |
| `brightness` | `float` | _required_ | The brightness, from 0.0 to 1.0. |

## Returns

`return red, green, blue`

| Value | Type | Description |
|---|---|---|
| red | `int` | The red component, from 0 to 255. |
| green | `int` | The green component, from 0 to 255. |
| blue | `int` | The blue component, from 0 to 255. |
