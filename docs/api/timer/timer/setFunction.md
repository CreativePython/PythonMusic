# setFunction()

Set the function the timer calls.

## Parameters

Once an object `timer` has been created, you can use the following functions:

```python
timer.setFunction(action)
```
```python
timer.setFunction(action, parameters)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call; it should accept as many parameters as the parameters list holds. |
| `parameters` | `list` | `None` | The parameters to pass to the function each time it is called. Defaults to none. |
