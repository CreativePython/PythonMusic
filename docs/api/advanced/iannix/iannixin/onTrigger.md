# onTrigger()

Set up a function to call when a given trigger fires in the IanniX score.

## Parameters

Once an object `iannixin` has been created, you can use the following function:

```python
iannixin.onTrigger(triggerID, action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `triggerID` | `int or str` | _required_ | The ID of the trigger to listen for. |
| `action` | `function` | _required_ | The function to call; it receives three parameters, x, y, and z, the trigger's coordinates. |
