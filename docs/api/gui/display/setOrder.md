# setOrder()

Move an object to a different layer within the display.

Layers run from smallest to largest, where 0 is closest to the front. Does nothing if the object is not in the display.

## Parameters

Once an object `display` has been created, you can use the following function:

```python
display.setOrder(item, order)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `item` | `Drawable` | _required_ | The object to re-layer. |
| `order` | `int` | _required_ | The layer to move it to; 0 is closest to the front. |
