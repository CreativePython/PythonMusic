# Point

Points are drawn at their center point (x, y).  Points behave like [Circles](../circle/index.md) that start with a 0 radius.

## Creating a Point

You can create a Point using the following functions:

```python
Point(x, y)
```

```python
Point(x, y, color, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `x` | `int or float` | _required_ | The horizontal position, in pixels. |
| `y` | `int or float` | _required_ | The vertical position, in pixels. |
| `color` | `Color` | `Color.BLACK` | The color. |
| `visibility` | `int` | `100` | How visible the point is, from 0 (invisible) to 100 (fully visible). |

For example,

```python
point = Point(50, 50)
```

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a Point has been created, the following functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Rotation](../../common/index.md#rotation-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Color](../../common/index.md#color-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)
