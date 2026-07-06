# setTarget()

Aim the ramp at a new value, starting from where it is now.

You can also change how long the ramp takes. If the ramp was not running, this starts it.

## Parameters

Once an object `linearramp` has been created, you can use the following functions:

```python
linearramp.setTarget(targetValue)
```
```python
linearramp.setTarget(targetValue, delay)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `targetValue` | `int or float` | _required_ | The new value to ramp toward. |
| `delay` | `int or float` | `None` | A new length for the ramp, in milliseconds. If omitted, the current length is kept. |
