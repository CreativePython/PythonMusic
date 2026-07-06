# OscillatorTimer

Call a function over and over with a value that oscillates between two bounds.

An OscillatorTimer moves a value smoothly up and down between a minimum and a maximum,
following a cosine wave, and calls your function with that value every delay
milliseconds. It is handy for fluctuating a sound's volume, panning, or frequency,
among other things. Start it with [start()](start.md), and stop it with [stop()](stop.md).

## Creating an OscillatorTimer

You can create an OscillatorTimer using the following function:

```python
OscillatorTimer(delay, minValue, maxValue, step, action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `delay` | `int or float` | _required_ | How long to wait between updates, in milliseconds. |
| `minValue` | `int or float` | _required_ | The lowest value to oscillate down to. |
| `maxValue` | `int or float` | _required_ | The highest value to oscillate up to. |
| `step` | `int or float` | _required_ | How far the value moves each update, from 0 to (maxValue - minValue). |
| `action` | `function` | _required_ | The function to call each update; it receives one parameter, the current value. |

For example,

```python
oscillatortimer = OscillatorTimer(100, 40, 100, 5, Play.setVolume)
```

## Functions

Once an OscillatorTimer `oscillatortimer` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`start()`](start.md) | Start the oscillator and begin calling your function. |
| [`stop()`](stop.md) | Stop the oscillator. |
| [`setDelay(delay)`](setDelay.md) | Set how long the oscillator waits between updates. |
| [`getDelay()`](getDelay.md) | Return how long the oscillator waits between updates. |
