# drawPoint()

Draw a single point straight onto the display.

This draws to the canvas and returns nothing, which is fast and best for shapes you will not change later. To keep a handle you can move or delete, create a [Point](../shapes/point/index.md) and [add()](add.md) it instead.

Erase these drawings with [clearDrawing()](clearDrawing.md).

## Parameters

Once an object `display` has been created, you can use the following functions:

```python
display.drawPoint(x, y)
```

```python
display.drawPoint(x, y, color, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x` | `int or float` | _required_ | The horizontal position, in pixels. |
| `y` | `int or float` | _required_ | The vertical position, in pixels. |
| `color` | `Color` | `Color.BLACK` | The color. |
| `visibility` | `int` | `100` | How visible the point is, from 0 (invisible) to 100 (fully visible). |