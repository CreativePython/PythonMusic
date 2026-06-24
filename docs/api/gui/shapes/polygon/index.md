# Polygon

Polygons are closed shapes, drawn using two parallel lists of x and y coordinates.  Unlike a [Polyline](../polyline/index.md), the shape is closed (the last corner joins back to the first).

## Creating a Polygon

You can create a Polygon using the following functions:

```python
Polygon(xPoints, yPoints)
```

```python
Polygon(xPoints, yPoints, color, fill, thickness, rotation, visibility)
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

For example,

```python
polygon = Polygon([312, 366, 510, 443], [244, 210, 312, 346])
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a Polygon has been created, the following functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Color](../../common/index.md#color-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
