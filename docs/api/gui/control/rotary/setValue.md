# setValue()

Set the rotary's value.

Moves the knob to match, and calls its update function.

## Parameters

Once an object `rotary` has been created, you can use the following function:

```python
rotary.setValue(newValue)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `newValue` | `int or float` | _required_ | The new value, between the rotary's minValue and maxValue. |
