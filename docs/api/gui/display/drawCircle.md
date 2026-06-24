# drawCircle()

Draw a circle straight onto the display.

This draws to the canvas and returns nothing, which is fast and best for shapes you will not change later. To keep a handle you can move or delete, create a [Circle](../shapes/circle/index.md) and [add()](add.md) it instead.

Erase these drawings with [clearDrawing()](clearDrawing.md).

## Parameters

Once an object `display` has been created, you can use the following functions:

```python
display.drawCircle(x, y, radius)
```

```python
display.drawCircle(x, y, radius, color, fill, thickness, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x` | `int or float` | _required_ | The horizontal position of the center, in pixels. |
| `y` | `int or float` | _required_ | The vertical position of the center, in pixels. |
| `radius` | `int or float` | _required_ | The radius, in pixels. |
| `color` | `Color` | `Color.BLACK` | The color. |
| `fill` | `bool` | `False` | Whether the circle is filled in (True) or just an outline (False). |
| `thickness` | `int` | `1` | The outline thickness, in pixels. |
| `visibility` | `int` | `100` | How visible the circle is, from 0 (invisible) to 100 (fully visible). |
