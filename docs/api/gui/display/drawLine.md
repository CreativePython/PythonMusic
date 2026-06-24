# drawLine()

Draw a line straight onto the display.

This draws to the canvas and returns nothing, which is fast and best for shapes you will not change later. To keep a handle you can move or delete, create a [Line](../shapes/line/index.md) and [add()](add.md) it instead.

Erase these drawings with [clearDrawing()](clearDrawing.md).

## Parameters

Once an object `display` has been created, you can use the following functions:

```python
display.drawLine(x1, y1, x2, y2)
```

```python
display.drawLine(x1, y1, x2, y2, color, thickness, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x1` | `int or float` | _required_ | The horizontal position of one end, in pixels. |
| `y1` | `int or float` | _required_ | The vertical position of one end, in pixels. |
| `x2` | `int or float` | _required_ | The horizontal position of the other end, in pixels. |
| `y2` | `int or float` | _required_ | The vertical position of the other end, in pixels. |
| `color` | `Color` | `Color.BLACK` | The color. |
| `thickness` | `int` | `1` | The line thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the line, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the line is, from 0 (invisible) to 100 (fully visible). |