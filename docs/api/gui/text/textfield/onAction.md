# onAction()

Register a function to call when the user presses Enter in the field.

## Parameters

Once an object `field` has been created, you can use the following function:

```python
field.onAction(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call when the user presses Enter in the field; it receives one parameter, the field's contents as a string. |
