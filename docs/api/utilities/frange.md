# frange()

Build a list of evenly spaced numbers, allowing fractional steps.

Like Python's range(), but step may be a fraction, for example 0.5. The numbers are rounded to the number of decimal places in step. As with range(), stop is not included, and step may be negative to count down.

## Parameters

```python
frange(start, stop, step)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `start` | `int or float` | _required_ | The first number. |
| `stop` | `int or float` | _required_ | The number to stop before (not included). |
| `step` | `int or float` | _required_ | The gap between numbers; may be negative to count down. Must not be zero. |

## Returns

`return floatList`

| Value | Type | Description |
|---|---|---|
| floatList | `list[float]` | The evenly spaced numbers from start up to (but not including) stop. |
