# addTrigger()

Add a trigger to the IanniX score at the given coordinates.

## Parameters

Once an object `iannixout` has been created, you can use the following function:

```python
iannixout.addTrigger(triggerID, x, y, z)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `triggerID` | `int or str` | _required_ | The ID to give the new trigger. |
| `x` | `float` | _required_ | The trigger's x coordinate. |
| `y` | `float` | _required_ | The trigger's y coordinate. |
| `z` | `float` | _required_ | The trigger's z coordinate. |
