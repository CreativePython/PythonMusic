# Icon

Create an image loaded from a file.

## Creating an Icon

You can create an Icon using the following functions:

```python
Icon(filename)
```

```python
Icon(filename, width, height, rotation, visibility)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `filename` | `str` | _required_ | The image file to load, ending in ".jpg" or ".png". |
| `width` | `int or float` | `None` | The width to scale the image to, in pixels. Defaults to the image's own width. |
| `height` | `int or float` | `None` | The height to scale the image to, in pixels. Defaults to the image's own height. |
| `backgroundColor` | `Color` | `None` | The color of the background behind the image.  Defaults to Color.CLEAR (no background). |
| `fill` | `bool` | `True` | Whether the background is filled in (`True`) or just an outline (`False`). |
| `thickness` | `int or float` | `0` | The background's outline thickness, in pixels. |
| `rotation` | `int or float` | `0` | How far to turn the image, in degrees, counter-clockwise. |
| `visibility` | `int` | `100` | How visible the image is, from 0 (invisible) to 100 (fully visible). |

For example,

```python
icon = Icon("mona-lisa.jpg")
```

Once created, you can add it to a [Display](../display/index.md) using the Display's [add()](../display/add.md) function.

## Functions

Once an Icon has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getPixel(column, row)`](getPixel.md) | Return the color of one pixel. |
| [`setPixel(column, row, color)`](setPixel.md) | Set the color of one pixel. |
| [`getPixels()`](getPixels.md) | Return every pixel in the image. |
| [`setPixels(pixels)`](setPixels.md) | Replace every pixel in the image. |
| [`getBackgroundColor()`](getBackgroundColor.md) | Return the icon's background color. |
| [`setBackgroundColor()`](setBackgroundColor.md) | Set the icon's background color. |
| [`crop(x, y, width, height)`](crop.md) | Crop the image to a rectangular region. |
| [`save(filename)`](save.md) | Save the image to a JPG or PNG file. |

Additionally, the following common functions are available:

- [Position](../common/index.md#position-functions)
- [Size](../common/index.md#size-functions)
- [Rotation](../common/index.md#rotation-functions)
- [Visibility](../common/index.md#visibility-functions)
- [Color](../common/index.md#color-functions)
- [Information](../common/index.md#information-functions)
- [Hit Testing](../common/index.md#hit-testing-functions)
- [Events](../common/index.md#event-functions)
