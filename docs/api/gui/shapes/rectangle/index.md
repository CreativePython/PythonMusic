# Rectangle

Rectangles are drawn between a starting point (x1, y1) and an ending point (x2, y2).

## Creating a Rectangle

You can create a Rectangle using the following functions:

```python
Rectangle(x1, y1, x2, y2)
```

```python
Rectangle(x1, y1, x2, y2, color, fill, thickness, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x1` | `int or float` | _required_ | The horizontal position of the top-left corner, in pixels. |
| `y1` | `int or float` | _required_ | The vertical position of the top-left corner, in pixels. |
| `x2` | `int or float` | _required_ | The horizontal position of the bottom-right corner, in pixels. |
| `y2` | `int or float` | _required_ | The vertical position of the bottom-right corner, in pixels. |
| `color` | `Color` | `Color.BLACK` | The color. |
| `fill` | `bool` | `False` | Whether the rectangle is filled in (True) or just an outline (False). |
| `thickness` | `int` | `1` | The outline thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the rectangle, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the rectangle is, from 0 (invisible) to 100 (fully visible). |

For example,

```python
rectangle = Rectangle(50, 30, 100, 150)
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a Rectangle has been created, the following functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Color](../../common/index.md#color-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
