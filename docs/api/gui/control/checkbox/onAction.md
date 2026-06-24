# onAction()

Register a function to call when the checkbox is checked or unchecked.

## Parameters

Once an object `checkbox` has been created, you can use the following function:

```python
checkbox.onAction(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call when the checkbox changes; it receives one parameter, `True` if it was just checked or `False` if it was just unchecked. |
