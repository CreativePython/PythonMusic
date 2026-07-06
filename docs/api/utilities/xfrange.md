# xfrange()

Step through evenly spaced numbers one at a time, allowing fractional steps.

A generator version of [frange()](frange.md): instead of building the whole list at once, it produces each number as you loop over it. This is handy for long ranges. As with range(), stop is not included, and step may be negative to count down.

## Parameters

```python
xfrange(start, stop, step)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `start` | `int or float` | _required_ | The first number. |
| `stop` | `int or float` | _required_ | The number to stop before (not included). |
| `step` | `int or float` | _required_ | The gap between numbers; may be negative to count down. Must not be zero. |

## Returns

`return value`

| Value | Type | Description |
|---|---|---|
| value | `float` | The next number in the sequence, each time through the loop. |
