# drawRectangle()

Draw a rectangle straight onto the display.

This draws to the canvas and returns nothing, which is fast and best for shapes you will not change later. To keep a handle you can move or delete, create a [Rectangle](../shapes/rectangle/index.md) and [add()](add.md) it instead.

Erase these drawings with [clearDrawing()](clearDrawing.md).

## Parameters

Once an object `display` has been created, you can use the following functions:

```python
display.drawRectangle(x1, y1, x2, y2)
```

```python
display.drawRectangle(x1, y1, x2, y2, color, fill, thickness, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x1` | `int or float` | _required_ | The horizontal position of the top-left corner, in pixels. |
| `y1` | `int or float` | _required_ | The vertical position of the top-left corner, in pixels. |
| `x2` | `int or float` | _required_ | The horizontal position of the bottom-right corner, in pixels. |
| `y2` | `int or float` | _required_ | The vertical position of the bottom-right corner, in pixels. |
| `color` | `Color` | `Color.BLACK` | The color. |
| `fill` | `bool` | `False` | Whether the rectangle is filled in (True) or just an outline (False). |
| `thickness` | `int` | `1` | The outline thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the rectangle, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the rectangle is, from 0 (invisible) to 100 (fully visible). |