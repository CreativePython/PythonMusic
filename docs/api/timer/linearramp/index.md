# LinearRamp

Slide a value smoothly from one number to another over time, calling a function as it changes.

A LinearRamp moves a value from a start to an end over a set time, calling your function with the current value at each small step along the way. This is handy for fading volume, moving graphics, and other gradual changes. Start it with [start()](start.md), and aim it somewhere new with [setTarget()](setTarget.md) while it runs.

## Creating a LinearRamp

You can create a LinearRamp using the following functions:

```python
LinearRamp(delay, startValue, endValue, action)
```
```python
LinearRamp(delay, startValue, endValue, action, step)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `delay` | `int or float` | _required_ | How long the whole ramp takes, in milliseconds. |
| `startValue` | `int or float` | _required_ | The value to start from. |
| `endValue` | `int or float` | _required_ | The value to end at. |
| `action` | `function` | _required_ | The function to call as the value changes; it receives one parameter, the current value. |
| `step` | `int` | `10` | How often to update the value and call the function, in milliseconds. |

For example,

```python
linearramp = LinearRamp(2000, 0, 127, Play.setVolume)
```

## Functions

Once a LinearRamp `linearramp` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`start()`](start.md) | Start the ramp from its current value toward its target. |
| [`stop()`](stop.md) | Stop the ramp where it is. |
| [`setTarget(targetValue)`](setTarget.md) | Aim the ramp at a new value, starting from where it is now. |
| [`setDuration(delay)`](setDuration.md) | Change how long the ramp takes. |
| [`isRunning()`](isRunning.md) | Report whether the ramp is running. |
| [`getCurrentValue()`](getCurrentValue.md) | Return the ramp's current value. |
