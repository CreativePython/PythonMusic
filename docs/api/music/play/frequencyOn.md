# frequencyOn()

Start a frequency sounding, and leave it sounding.

Stop it with [Play.frequencyOff()](frequencyOff.md). Play only one frequency per channel at a time:
since this uses pitch bend, it affects every other note sounding on the channel.

## Parameters

`Play.frequencyOn()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.frequencyOn(frequency)
```
```python
Play.frequencyOn(frequency, velocity, channel, panning)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `frequency` | `float` | _required_ | The frequency to play, in hertz (8.17 to 12600.0). |
| `velocity` | `int` | `100` | How loud the note is, from 0 to 127. |
| `channel` | `int` | `0` | The channel to play on, from 0 to 15. |
| `panning` | `int` | `-1` | Stereo position from 0 (left) to 127 (right); -1 uses the global panning. |
