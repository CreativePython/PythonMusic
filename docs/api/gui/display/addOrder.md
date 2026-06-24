# addOrder()

Add an object to the display on a given layer.

Same as [add()](add.md), but also sets the object's layer within the display. Layers run from smallest to largest, where 0 is closest to the front.

## Parameters

Once an object `display` has been created, you can use the following function:

```python
display.addOrder(item, order)
```

```python
display.addOrder(item, order, x, y)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `item` | `Drawable` | _required_ | The object to add. |
| `order` | `int` | _required_ | The layer to place it on; 0 is closest to the front. |
| `x` | `int or float` | `None` | The horizontal position, in pixels. Defaults to the object's current position. |
| `y` | `int or float` | `None` | The vertical position, in pixels. Defaults to the object's current position. |