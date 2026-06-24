# drawArcCircle()

Draw a circular arc straight onto the display.  Like [drawArc()](drawArc.md), but the arc is part of a circle given by its center and radius.

Angles are in degrees, with 0 at the three o'clock position; a positive angle goes counter-clockwise, a negative one clockwise. The constants `HALF_PI`, `PI`, and `TWO_PI` may be used for the angles.

This draws to the canvas and returns nothing, which is fast and best for shapes you will not change later. To keep a handle you can move or delete, create an [ArcCircle](../shapes/arccircle/index.md) and [add()](add.md) it instead.

Erase these drawings with [clearDrawing()](clearDrawing.md).

## Parameters

Once an object `display` has been created, you can use the following functions:

```python
display.drawArcCircle(x, y, radius)
```

```python
display.drawArcCircle(x, y, radius, startAngle=PI, endAngle=TWO_PI, style=OPEN, color=Color.BLACK, fill=False, thickness=1, rotation=0, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x` | `int or float` | _required_ | The horizontal position of the center, in pixels. |
| `y` | `int or float` | _required_ | The vertical position of the center, in pixels. |
| `radius` | `int or float` | _required_ | The radius, in pixels. |
| `startAngle` | `int or float` | `PI` | The starting angle, in degrees. |
| `endAngle` | `int or float` | `TWO_PI` | The ending angle, in degrees. |
| `style` | `int` | `OPEN` | The arc style, one of OPEN (an open arc), CHORD (closed with a straight line between the ends), or PIE (closed with two lines to the center). |
| `color` | `Color` | `Color.BLACK` | The color. |
| `fill` | `bool` | `False` | Whether the arc is filled in (True) or just an outline (False). |
| `thickness` | `int` | `1` | The outline thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the arc, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the arc is, from 0 (invisible) to 100 (fully visible). |
