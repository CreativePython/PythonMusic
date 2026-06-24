# add()

Add an object to a display.

If x and y are specified, the object is added at that position.  Otherwise, it uses its current position.

If the object is already in another Display or [Group](../group/index.md), it is removed from there first.

## Parameters

Once an object `display` has been created, you can use the following functions:

```python
display.add(item)
```

```python
display.add(item, x, y)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `item` | `Drawable` | _required_ | The object to add. |
| `x` | `int or float` | `None` | The horizontal position, in pixels. Defaults to the object's current position. |
| `y` | `int or float` | `None` | The vertical position, in pixels. Defaults to the object's current position. |