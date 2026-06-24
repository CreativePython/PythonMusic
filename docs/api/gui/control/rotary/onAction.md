# onAction()

Register a function to call when the knob turns

## Parameters

Once an object `rotary` has been created, you can use the following function:

```python
rotary.onAction(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call when the knob turns; it receives the new value. |
