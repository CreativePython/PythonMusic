# onAction()

Register a function to call when an item is picked.

## Parameters

Once an object `dropdown` has been created, you can use the following function:

```python
dropdown.onAction(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call when an item is picked; it receives one parameter, the selected item as a string. |
