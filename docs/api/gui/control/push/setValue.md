# setValue()

Set whether the push button is pressed.

Redraws the push button to match, and calls its update function.

## Parameters

Once an object `push` has been created, you can use the following function:

```python
push.setValue(newValue)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `newValue` | `bool` | _required_ | `True` to push the button, `False` to release it. |
