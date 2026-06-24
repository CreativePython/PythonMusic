# setValue()

Set the fader's value.

Moves the fader bar to match, and calls its update function.

## Parameters

Once an object `fader` has been created, you can use the following function:

```python
fader.setValue(newValue)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `newValue` | `int or float` | _required_ | The new value, between the fader's minValue and maxValue. |
