# onCursor()

Set up a function to call as a given cursor moves through the IanniX score.

## Parameters

Once an object `iannixin` has been created, you can use the following function:

```python
iannixin.onCursor(cursorID, action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `cursorID` | `int or str` | _required_ | The ID of the cursor to listen for. |
| `action` | `function` | _required_ | The function to call; it receives three parameters, x, y, and z, the cursor's current coordinates. |
