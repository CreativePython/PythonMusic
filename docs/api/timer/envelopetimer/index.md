# EnvelopeTimer

Call a function with a series of values, each delivered at its own time.

An EnvelopeTimer steps your function through a list of values at a matching list of times, and can cycle back to the start after the last value. It is handy for shaping a sound's volume, panning, or frequency over time. The values and times lists run in parallel, and the times are absolute milliseconds from the start, in increasing order.

A value that is itself a list or tuple is unpacked into several arguments to the function. Start it with [start()](start.md), and stop it with [stop()](stop.md).

## Creating an EnvelopeTimer

You can create an EnvelopeTimer using the following functions:

```python
EnvelopeTimer(action, values, times)
```
```python
EnvelopeTimer(action, values, times, repeat)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call; it receives the current value, or several arguments if the value is a list or tuple. |
| `values` | `list` | _required_ | The values to deliver, in order. |
| `times` | `list[int or float]` | _required_ | When to deliver each value, in milliseconds from the start; each must be later than the one before. |
| `repeat` | `bool` | `False` | Whether to cycle back to the start after the last value (True) or stop (False). |

For example,

```python
envelopetimer = EnvelopeTimer(Play.setVolume, [127, 0], [0, 1000])
```

## Functions

Once an EnvelopeTimer `envelopetimer` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`start()`](start.md) | Start the envelope from the beginning. |
| [`stop()`](stop.md) | Stop the envelope and reset it to the beginning. |
| [`pause()`](pause.md) | Pause the envelope, remembering where it is. |
| [`resume()`](resume.md) | Resume the envelope from where it was paused. |
| [`isRunning()`](isRunning.md) | Report whether the envelope is running. |
| [`isPaused()`](isPaused.md) | Report whether the envelope is paused. |
