# addWithValues()

Step a function through a list of values, evenly spaced over time.

Calls the function once for each value in turn, handing it the current value. Good for sweeping a setting smoothly through a series of numbers.

## Parameters

`Automate.addWithValues()` is a static utility. Call it on the `Automate` class itself, for example:

```python
Automate.addWithValues(action, values)
```
```python
Automate.addWithValues(action, values, duration, repeat, whenDone)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call; it receives one parameter, the current value. |
| `values` | `list` | _required_ | The values to step through, in order. |
| `duration` | `int or float` | `None` | How long the whole list takes, in seconds. If omitted, one value is delivered per frame. |
| `repeat` | `int` | `1` | How many times to run through the list; use -1 to repeat forever. |
| `whenDone` | `function` | `None` | A function to call once, after the last run through the list; it receives no parameters. |
