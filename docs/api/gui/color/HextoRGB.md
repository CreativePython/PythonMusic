# HextoRGB()

Convert a hex color string to RGB.

The leading "#" is optional.

## Parameters

`Color.HextoRGB()` is a static utility. Call it on the `Color` class itself, for example:

```python
Color.HextoRGB(hex)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hex` | `str` | _required_ | A hex color string, for example "#ff8800". |

## Returns

`return red, green, blue`

| Value | Type | Description |
|---|---|---|
| red | `int` | The red component, from 0 to 255. |
| green | `int` | The green component, from 0 to 255. |
| blue | `int` | The blue component, from 0 to 255. |
