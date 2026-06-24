# Arc

Create an arc, part of an oval that fills the box given by two opposite corners.

Arcs are drawn between a starting point (x1, y1) and an ending point (x2, y2).  They look like [Ovals](../oval/index.md), except only the section from `startAngle` to `endAngle` is visible.

## Creating an Arc

You can create an Arc using the following functions:

```python
Arc(x1, y1, x2, y2)
```

```python
Arc(x1, y1, x2, y2, startAngle, endAngle, style, color, fill, thickness, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x1` | `int or float` | _required_ | The horizontal position of the box's top-left corner, in pixels. |
| `y1` | `int or float` | _required_ | The vertical position of the box's top-left corner, in pixels. |
| `x2` | `int or float` | _required_ | The horizontal position of the box's bottom-right corner, in pixels. |
| `y2` | `int or float` | _required_ | The vertical position of the box's bottom-right corner, in pixels. |
| `startAngle` | `int or float` | `PI` | The starting angle, in degrees. |
| `endAngle` | `int or float` | `TWO_PI` | The ending angle, in degrees. |
| `style` | `int` | `OPEN` | The arc style, one of OPEN (an open arc), CHORD (closed with a straight line between the ends), or PIE (closed with two lines to the center). |
| `color` | `Color` | `Color.BLACK` | The color. |
| `fill` | `bool` | `False` | Whether the arc is filled in (True) or just an outline (False). |
| `thickness` | `int` | `1` | The outline thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the arc, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the arc is, from 0 (invisible) to 100 (fully visible). |

For example,

```python
arc = Arc(100, 100, 200, 200, 0, 180)
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once an Arc has been created, the following functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Color](../../common/index.md#color-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
