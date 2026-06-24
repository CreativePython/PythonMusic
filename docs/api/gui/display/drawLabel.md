# drawLabel()

Draw a line of text straight onto the display.

This draws to the canvas and returns nothing, which is fast and best for text you will not change later. To keep a handle you can move or delete, create a [Label](../text/label/index.md) and [add()](add.md) it instead.

Erase these drawings with [clearDrawing()](clearDrawing.md).

## Parameters

Once an object `display` has been created, you can use the following functions:

```python
display.drawLabel(text, x, y)
```

```python
display.drawLabel(text, x, y, color, font, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `text` | `str` | _required_ | The text to draw. |
| `x` | `int or float` | _required_ | The horizontal position of the top-left corner, in pixels. |
| `y` | `int or float` | _required_ | The vertical position of the top-left corner, in pixels. |
| `color` | `Color` | `Color.BLACK` | The text color. |
| `font` | `Font` | `None` | The font, for example `Font("Serif", Font.ITALIC, 16)`. If omitted, the default font is used. |
| `visibility` | `int` | `100` | How visible the label is, from 0 (invisible) to 100 (fully visible). |