# addOrder()

Add an object to the group on a given layer.

Same as [add()](add.md), but also sets the object's layer within the group. Layers run from smallest to largest, where 0 is closest to the front.

## Parameters

Once an object `group` has been created, you can use the following function:

```python
group.addOrder(item, order)
```

```python
group.addOrder(item, order, x, y)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `item` | `Drawable` | _required_ | The object to add. |
| `order` | `int` | _required_ | The layer to place it on; 0 is closest to the front. |
| `x` | `int or float` | `None` | The horizontal position, in pixels. Defaults to the object's current position. |
| `y` | `int or float` | `None` | The vertical position, in pixels. Defaults to the object's current position. |