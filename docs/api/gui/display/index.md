# Display

A Display is the window your GUI objects appear in. Build a GUI by adding shapes, images, text, and controls to it with [add()](add.md). The window opens as soon as you create it. Inside the display the origin (0, 0) is the top-left corner; x increases to the right and y increases downward.

A program may have several displays open. Displays may contain any number of GUI objects, but they cannot contain another display.

Once a display has been created, you populate it by placing various GUI widgets and graphics objects on it. The library provides various GUI widgets and graphics objects.

## Creating a Display

You can create a Display using the following functions:

```python
Display()
```

```python
Display(title, width, height, x, y, color)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `title` | `str` | `''` | The window title. |
| `width` | `int or float` | `600` | The window width, in pixels. |
| `height` | `int or float` | `400` | The window height, in pixels. |
| `x` | `int or float` | `0` | The horizontal position of the window's top-left corner on the screen, in pixels. |
| `y` | `int or float` | `50` | The vertical position of the window's top-left corner on the screen, in pixels. |
| `color` | `Color` | `Color.WHITE` | The background color. |

For example,

```python
display = Display("Simple GUI", 120, 60)
```

## Functions

Once a Display has been created, the following functions are available:

| Function | Description |
|---|---|
| [`add(item)`](add.md) | Add an object to the display. |
| [`remove(item)`](remove.md) | Remove an object from the display. |
| [`removeAll()`](removeAll.md) | Remove every object from the display. |
| [`getItems()`](getItems.md) | Return the objects currently in the display. |

### Layering GUI Objects

GUI objects on a Display are layered. Typically, the most recent object sits on top of the others (`order = 0`). You can change the order

| Function | Description |
|---|---|
| [`addOrder(item, order)`](addOrder.md) | Add an object to the display on a given layer. |
| [`getOrder(item)`](getOrder.md) | Return the layer an object sits on within the display. |
| [`setOrder(item, order)`](setOrder.md) | Move an object to a different layer within the display. |

### Manipulating the Display

These common functions are useful for updating how a Display appears on the screen.

- [Position](../common/index.md#position-functions)
- [Size](../common/index.md#size-functions)
- [Events](../common/index.md#event-functions)

Additionally, the following functions are available:

| Function | Description |
|---|---|
| [`getTitle()`](getTitle.md) | Return the display's title. |
| [`setTitle(title)`](setTitle.md) | Set the display's title. |
| [`getColor()`](getColor.md) | Return the display's background color. |
| [`setColor()`](setColor.md) | Set the display's background color. |
| [`show()`](show.md) | Show the display. |
| [`hide()`](hide.md) | Hide the display. |
| [`close()`](close.md) | Close the display. |
| [`save(filename)`](save.md) | Save a picture of the display to an image file. |
| [`setToolTipText()`](setToolTipText.md) | Set the hover text shown over the display. |
| [`showMouseCoordinates()`](showMouseCoordinates.md) | Show the mouse position in the display's tooltip as the mouse moves. |
| [`hideMouseCoordinates()`](hideMouseCoordinates.md) | Stop showing the mouse position in the display's tooltip. |

### Adding Menus

[Menu](../control/menu/index.md) objects are different from other GUI objects; instead of appearing on a Display, menu objects are added to the Display's menu bar, or as context (right click, pop-up) menus.

| Function | Description |
|---|---|
| [`addMenu(menu)`](addMenu.md) | Add a menu to the display's menu bar. |
| [`addPopupMenu(menu)`](addPopupMenu.md) | Add a pop-up (right-click) menu to the display. |

### Drawing Shapes

In addition to adding movable GUI objects to a Display, you can also draw shapes and text directly to the Display's background.  Drawing shapes is faster than adding GUI objects, but drawn shapes can't be moved or erased without clearing the entire canvas (using [clearDrawing()](clearDrawing.md)).

| Function | Description |
|---|---|
| [`drawRectangle(x1, y1, x2, y2)`](drawRectangle.md) | Draw a rectangle straight onto the display. |
| [`drawOval(x1, y1, x2, y2)`](drawOval.md) | Draw an oval straight onto the display. |
| [`drawCircle(x, y, radius)`](drawCircle.md) | Draw a circle straight onto the display. |
| [`drawPoint(x, y)`](drawPoint.md) | Draw a single point straight onto the display. |
| [`drawArc(x1, y1, x2, y2)`](drawArc.md) | Draw an arc straight onto the display. |
| [`drawArcCircle(x, y, radius)`](drawArcCircle.md) | Draw a circular arc straight onto the display. |
| [`drawPolyline(xPoints, yPoints)`](drawPolyline.md) | Draw a connected series of line segments straight onto the display. |
| [`drawLine(x1, y1, x2, y2)`](drawLine.md) | Draw a line straight onto the display. |
| [`drawPolygon(xPoints, yPoints)`](drawPolygon.md) | Draw a polygon straight onto the display. |
| [`drawIcon(filename, x, y)`](drawIcon.md) | Draw an image straight onto the display. |
| [`drawLabel(text, x, y)`](drawLabel.md) | Draw a line of text straight onto the display. |
| [`drawText(text, x, y)`](drawText.md) | Draw a line of text straight onto the display. |
| [`clearDrawing()`](clearDrawing.md) | Erase everything drawn with the draw functions. |
