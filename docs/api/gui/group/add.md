# add()

Add an object to a group.

If x and y are specified, the object is added at that position.  Otherwise, it uses its current position.

If the object is already in another Group or [Display](../display/index.md), it is removed from there first.

## Parameters

Once an object `group` has been created, you can use the following functions:

```python
group.add(item)
```

```python
group.add(item, x, y)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `item` | `Drawable` | _required_ | The object to add. |
| `x` | `int or float` | `None` | The horizontal position, in pixels. Defaults to the object's current position. |
| `y` | `int or float` | `None` | The vertical position, in pixels. Defaults to the object's current position. |