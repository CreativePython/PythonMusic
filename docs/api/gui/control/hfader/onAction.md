# onAction()

Register a function to call when the fader moves.

## Parameters

Once an object `fader` has been created, you can use the following function:

```python
fader.onAction(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call when the fader moves; it receives the new value. |
