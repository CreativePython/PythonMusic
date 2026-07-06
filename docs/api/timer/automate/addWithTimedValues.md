# addWithTimedValues()

Step a function through a list of values, each delivered at its own time.

Like [addWithValues()](addWithValues.md), but you give the exact moment for each value instead of spacing them evenly. The values and times lists are parallel, and the times must increase.

## Parameters

`Automate.addWithTimedValues()` is a static utility. Call it on the `Automate` class itself, for example:

```python
Automate.addWithTimedValues(action, values, times)
```
```python
Automate.addWithTimedValues(action, values, times, duration, repeat, whenDone)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call; it receives one parameter, the current value. |
| `values` | `list` | _required_ | The values to step through, in order. |
| `times` | `list[int or float]` | _required_ | When to deliver each value, in seconds from the start of the sequence; each must be later than the one before. |
| `duration` | `int or float` | `None` | Stretch or squeeze the whole sequence to last this many seconds. If omitted, the times are used as given. |
| `repeat` | `int` | `1` | How many times to run through the sequence; use -1 to repeat forever. |
| `whenDone` | `function` | `None` | A function to call once, after the last run through the sequence; it receives no parameters. |
