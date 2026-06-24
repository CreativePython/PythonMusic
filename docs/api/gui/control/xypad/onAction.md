# onAction()

Register a function to call when the tracker moves.

## Parameters

Once an object `xypad` has been created, you can use the following function:

```python
xypad.onAction(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call when the tracker moves; it receives the new [x, y] value. |
