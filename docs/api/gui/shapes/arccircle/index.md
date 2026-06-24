# ArcCircle

Create an ArcCircle, part of a circle around a center and radius.

ArcCircles are like [Arcs](../arc/index.md), but shaped from a circle instead of an oval.  They look like [Circles](../circle/index.md), except only the section from `startAngle` to `endAngle` is visible.

## Creating an ArcCircle

You can create an ArcCircle using the following functions:

```python
ArcCircle(x, y, radius)
```

```python
ArcCircle(x, y, radius, startAngle, endAngle, style, color, fill, thickness, rotation, visibility)
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

For example,

```python
arc = ArcCircle(100, 100, 20, 0, 180)
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once an ArcCircle has been created, the following functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Color](../../common/index.md#color-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
