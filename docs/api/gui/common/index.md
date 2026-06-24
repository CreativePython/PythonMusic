# Common Functions

Many functions are shared across multiple objects in the GUI library.

## Position Functions

| Function | Description |
|---|---|
| [`move(x, y)`](position/move.md) | Move the object to a new position. |
| [`getPosition()`](position/getPosition.md) | Return the object's position, the top-left corner of its bounding box. |
| [`setPosition(x, y)`](position/setPosition.md) | Move the object so the top-left corner of its bounding box sits at the given point. |
| [`getX()`](position/getX.md) | Return the object's horizontal position. |
| [`setX(x)`](position/setX.md) | Set the object's horizontal position. |
| [`getY()`](position/getY.md) | Return the object's vertical position. |
| [`setY(y)`](position/setY.md) | Set the object's vertical position. |
| [`getCenter()`](position/getCenter.md) | Return the object's center point. |
| [`setCenter(x, y)`](position/setCenter.md) | Move the object so its center sits at the given point. |
| [`getCenterX()`](position/getCenterX.md) | Return the object's horizontal center. |
| [`setCenterX(x)`](position/setCenterX.md) | Set the object's horizontal center. |
| [`getCenterY()`](position/getCenterY.md) | Return the object's vertical center. |
| [`setCenterY(y)`](position/setCenterY.md) | Set the object's vertical center. |
| [`getEndpoints()`](position/getEndpoints.md) | Return the object's endpoints. |
| [`getBoundingBox()`](position/getBoundingBox.md) | Return the smallest upright box that surrounds the object. |

## Size Functions

| Function | Description |
|---|---|
| [`getSize()`](size/getSize.md) | Return the object's width and height. |
| [`setSize(width, height)`](size/setSize.md) | Set the object's width and height. |
| [`getWidth()`](size/getWidth.md) | Return the object's width. |
| [`setWidth(width)`](size/setWidth.md) | Set the object's width. |
| [`getHeight()`](size/getHeight.md) | Return the object's height. |
| [`setHeight(height)`](size/setHeight.md) | Set the object's height. |
| [`getRadius()`](size/getRadius.md) | Return the circle's radius. |
| [`setRadius(radius)`](size/setRadius.md) | Set the circle's radius. |
| [`getLength()`](size/getLength.md) | Return the line's length. |
| [`setLength(length)`](size/setLength.md) | Set the line's length. |

## Rotation Functions

| Function | Description |
|---|---|
| [`getRotation()`](rotation/getRotation.md) | Return how far the object is turned. |
| [`setRotation(rotation)`](rotation/setRotation.md) | Turn the object to a given angle. |
| [`rotate(angle)`](rotation/rotate.md) | Turn the object by an additional angle. |

## Visibility Functions

| Function | Description |
|---|---|
| [`getVisibility()`](visibility/getVisibility.md) | Return how visible the object is. |
| [`setVisibility(visibility)`](visibility/setVisibility.md) | Set how visible the object is. |

## Color Functions

| Function | Description |
|---|---|
| [`getColor()`](color/getColor.md) | Return the object's color. |
| [`setColor(color)`](color/setColor.md) | Set the object's color. |
| [`getFill()`](color/getFill.md) | Report whether the object is filled in. |
| [`setFill(fill)`](color/setFill.md) | Set whether the object is filled in. |
| [`getThickness()`](color/getThickness.md) | Return the object's outline thickness. |
| [`setThickness(thickness)`](color/setThickness.md) | Set the object's outline thickness. |

## Information Functions

| Function | Description |
|---|---|
| [`getGroup()`](information/getGroup.md) | Return the Group this object belongs to. |
| [`getDisplay()`](information/getDisplay.md) | Return the Display this object is on. |
| [`setToolTipText(text)`](information/setToolTipText.md) | Set the hover text shown over the object. |

## Hit-Testing Functions

| Function | Description |
|---|---|
| [`contains(x, y)`](hit-testing/contains.md) | Report whether a point lies inside the object. |
| [`intersects(other)`](hit-testing/intersects.md) | Report whether this object overlaps another. |
| [`encloses(other)`](hit-testing/encloses.md) | Report whether this object completely contains another. |

## Event Functions

Event functions are used to set callback functions that are called whenever something happens, such as the mouse moving or a key being pressed.

### Mouse Events

See [Mouse Events](../event/mouse/index.md) for more information on how to use mouse events.

| Function | Description |
|---|---|
| [`onMouseClick(action)`](events/mouse/onMouseClick.md) | Register a function to call when the mouse is clicked (pressed down and released) on this object. |
| [`onMouseDown(action)`](events/mouse/onMouseDown.md) | Register a function to call when the mouse button is pressed on this object. |
| [`onMouseUp(action)`](events/mouse/onMouseUp.md) | Register a function to call when the mouse button is released over this object. |
| [`onMouseMove(action)`](events/mouse/onMouseMove.md) | Register a function to call when the mouse moves over this object. |
| [`onMouseDrag(action)`](events/mouse/onMouseDrag.md) | Register a function to call when the mouse is dragged over this object. |
| [`onMouseEnter(action)`](events/mouse/onMouseEnter.md) | Register a function to call when the mouse moves onto this object. |
| [`onMouseExit(action)`](events/mouse/onMouseExit.md) | Register a function to call when the mouse moves off this object. |

### Keyboard Events

See [Keyboard Events](../event/keyboard/index.md) for more information on how to use keyboard events.

| Function | Description |
|---|---|
| [`onKeyType(action)`](events/keyboard/onKeyType.md) | Register a function to call when a key is typed (pressed and released). |
| [`onKeyDown(action)`](events/keyboard/onKeyDown.md) | Register a function to call when a key is pressed down. |
| [`onKeyUp(action)`](events/keyboard/onKeyUp.md) | Register a function to call when a key is released. |
