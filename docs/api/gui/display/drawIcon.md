# drawIcon()

Draw an icon straight onto the display.

This draws to the canvas and returns nothing, which is fast and best for images you will not change later. To keep a handle you can move or delete, create an [Icon](../icon/index.md) and [add()](add.md) it instead.

Erase these drawings with [clearDrawing()](clearDrawing.md).

## Parameters

Once an object `display` has been created, you can use the following functions:

```python
display.drawIcon(filename, x, y)
```

```python
display.drawIcon(filename, x, y, width, height, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `filename` | `str` | _required_ | The image file to load, ending in ".jpg" or ".png". |
| `x` | `int or float` | _required_ | The horizontal position of the top-left corner, in pixels. |
| `y` | `int or float` | _required_ | The vertical position of the top-left corner, in pixels. |
| `width` | `int or float` | `None` | The width to scale the image to, in pixels. Defaults to the image's own width. |
| `height` | `int or float` | `None` | The height to scale the image to, in pixels. Defaults to the image's own height. |
| `rotation` | `int or float` | `0` | How far to turn the image, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the icon is, from 0 (invisible) to 100 (fully visible). |
