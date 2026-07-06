# gradient()

Create a smooth run of colors blending from one color to another.

The blend is computed in a perceptual color space, so the steps look evenly spaced to the eye. Also available as colorGradient().

## Parameters

`Color.gradient()` is a static utility. Call it on the `Color` class itself, for example:

```python
Color.gradient(startColor, endColor, steps)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `startColor` | `Color or list[int]` | _required_ | The starting color, as a Color or an [red, green, blue] list. |
| `endColor` | `Color or list[int]` | _required_ | The ending color, as a Color or an [red, green, blue] list. |
| `steps` | `int` | _required_ | How many colors to produce. |

## Returns

`return gradientList`

| Value | Type | Description |
|---|---|---|
| gradientList | `list[Color] or list[list[int]]` | The blended colors. These are Color objects if you passed Color objects, otherwise [red, green, blue] lists. |
