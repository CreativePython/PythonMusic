# Color

Represent a color as red, green, and blue components, with optional transparency.

Use red, green, and blue to build a color directly. Leave any of the three out and a color-selection dialog opens for you to pick one instead.

Ready-made constants are also available:

```python
Color.BLACK,  Color.BLUE,   Color.CYAN,       Color.DARK_GRAY,
Color.GRAY,   Color.GREEN,  Color.LIGHT_GRAY, Color.MAGENTA,
Color.ORANGE, Color.PINK,   Color.PURPLE,     Color.RED,
Color.WHITE,  Color.YELLOW, Color.CLEAR
```

All [GUI Shapes](../shapes/index.md) and many other GUI objects use functions like [setColor()](../common/color/setColor.md) and [getColor()](../common/color/getColor.md) with Color objects.

## Creating a Color

You can create a Color using the following functions:

```python
Color()
```

```python
Color(red, green, blue)
```

```python
Color(red, green, blue, alpha)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `red` | `int` | `None` | The red component, from 0 to 255. If omitted, a color-selection dialog opens. |
| `green` | `int` | `None` | The green component, from 0 to 255. If omitted, a color-selection dialog opens. |
| `blue` | `int` | `None` | The blue component, from 0 to 255. If omitted, a color-selection dialog opens. |
| `alpha` | `int` | `255` | The opacity, from 0 (fully transparent) to 255 (fully opaque). |

For example,

```python
color1 = Color(255, 255, 255)        # same as Color.WHITE
color2 = Color(255, 255, 255, 150)   # same as Color.WHITE, but semi-transparent
```

## Functions

Once a Color has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getRed()`](getRed.md) | Return the red component of the color. |
| [`setRed(red)`](setRed.md) | Set the red component of the color. |
| [`getGreen()`](getGreen.md) | Return the green component of the color. |
| [`setGreen(green)`](setGreen.md) | Set the green component of the color. |
| [`getBlue()`](getBlue.md) | Return the blue component of the color. |
| [`setBlue(blue)`](setBlue.md) | Set the blue component of the color. |
| [`getAlpha()`](getAlpha.md) | Return the alpha (transparency) component of the color. |
| [`setAlpha(alpha)`](setAlpha.md) | Set the alpha (transparency) component of the color. |
| [`getRGB()`](getRGB.md) | Return the color's red, green, and blue components together. |
| [`getRGBA()`](getRGBA.md) | Return the color's red, green, blue, and alpha components together. |
| [`brighter()`](brighter.md) | Return a brighter version of the color. |
| [`darker()`](darker.md) | Return a darker version of the color. |

## Static Functions

Color has static functions as well - you don't need to create a Color object to use them.  Call these functions on the class itself (for example, [Color.gradient()](gradient.md)). 

| Function | Description |
|---|---|
| [`select()`](select.md) | Open a color-selection dialog and return the RGB values the user picks. |
| [`gradient(startColor, endColor, steps)`](gradient.md) | Create a smooth run of colors blending from one color to another. |
| [`getHSBColor(hue, saturation, brightness)`](getHSBColor.md) | Create a Color from HSB (hue, saturation, brightness) values. |
| [`HSBtoRGB(hue, saturation, brightness)`](HSBtoRGB.md) | Convert a color from HSB (hue, saturation, brightness) to RGB. |
| [`RGBtoHSB(red, green, blue)`](RGBtoHSB.md) | Convert a color from RGB to HSB (hue, saturation, brightness). |
| [`getHexColor(hex)`](getHexColor.md) | Create a Color from a hex color string. |
| [`HextoRGB(hex)`](HextoRGB.md) | Convert a hex color string to RGB. |
| [`RGBtoHex(red, green, blue)`](RGBtoHex.md) | Convert red, green, and blue values to a hex color string. |
