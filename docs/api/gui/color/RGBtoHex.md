# RGBtoHex()

Convert red, green, and blue values to a hex color string.

## Parameters

`Color.RGBtoHex()` is a static utility. Call it on the `Color` class itself, for example:

```python
Color.RGBtoHex(red, green, blue)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `red` | `int` | _required_ | The red component, from 0 to 255. |
| `green` | `int` | _required_ | The green component, from 0 to 255. |
| `blue` | `int` | _required_ | The blue component, from 0 to 255. |

## Returns

`return hexCode`

| Value | Type | Description |
|---|---|---|
| hexCode | `str` | A hex color string, for example "#ff8800". |
