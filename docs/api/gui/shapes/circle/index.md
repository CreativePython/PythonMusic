# Circle

Circles are drawn with a radius around a center point (x, y).

## Creating a Circle

You can create a Circle using the following functions:

```python
Circle(x, y, radius)
```

```python
Circle(x, y, radius, color, fill, thickness, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x` | `int or float` | _required_ | The horizontal position of the center, in pixels. |
| `y` | `int or float` | _required_ | The vertical position of the center, in pixels. |
| `radius` | `int or float` | _required_ | The radius, in pixels. |
| `color` | `Color` | `Color.BLACK` | The color. |
| `fill` | `bool` | `False` | Whether the circle is filled in (True) or just an outline (False). |
| `thickness` | `int` | `1` | The outline thickness, in pixels. |
| `visibility` | `int` | `100` | How visible the circle is, from 0 (invisible) to 100 (fully visible). |

For example,

```python
circle = Circle(50, 50, 5)
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a Circle has been created, the following functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Color](../../common/index.md#color-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
