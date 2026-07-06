# note()

Schedule a note to play after a delay and last a set time.

## Parameters

`Play.note()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.note(pitch, start, duration)
```
```python
Play.note(pitch, start, duration, velocity, channel, panning)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int or float` | _required_ | A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0) to reach pitches between the standard notes. |
| `start` | `int or float` | _required_ | How long from now the note begins, in milliseconds. |
| `duration` | `int or float` | _required_ | How long the note lasts, in milliseconds. |
| `velocity` | `int` | `100` | How loud the note is, from 0 to 127. |
| `channel` | `int` | `0` | The channel to play on, from 0 to 15. |
| `panning` | `int` | `-1` | Stereo position from 0 (left) to 127 (right); -1 uses the global panning. |
