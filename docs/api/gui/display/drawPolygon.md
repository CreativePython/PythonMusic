# drawPolygon()

Draw a polygon straight onto the display.

The xPoints and yPoints lists are parallel: the first corner is (xPoints[0], yPoints[0]), the next is (xPoints[1], yPoints[1]), and so on.

This draws to the canvas and returns nothing, which is fast and best for shapes you will not change later. To keep a handle you can move or delete, create a [Polygon](../shapes/polygon/index.md) and [add()](add.md) it instead.

Erase these drawings with [clearDrawing()](clearDrawing.md).

## Parameters

Once an object `display` has been created, you can use the following functions:

```python
display.drawPolygon(xPoints, yPoints)
```

```python
display.drawPolygon(xPoints, yPoints, color, fill, thickness, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `xPoints` | `list[int or float]` | _required_ | The horizontal positions of the corners, in pixels. |
| `yPoints` | `list[int or float]` | _required_ | The vertical positions of the corners, in pixels. |
| `color` | `Color` | `Color.BLACK` | The color. |
| `fill` | `bool` | `False` | Whether the polygon is filled in (True) or just an outline (False). |
| `thickness` | `int` | `1` | The outline thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the polygon, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the polygon is, from 0 (invisible) to 100 (fully visible). |
