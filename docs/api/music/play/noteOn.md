# noteOn()

Start a pitch sounding, and leave it sounding.

The note keeps playing until you stop it with [Play.noteOff()](noteOff.md).

## Parameters

`Play.noteOn()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.noteOn(pitch)
```
```python
Play.noteOn(pitch, velocity, channel, panning)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int or float` | _required_ | A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0) to reach pitches between the standard notes. |
| `velocity` | `int` | `100` | How loud the note is, from 0 to 127. |
| `channel` | `int` | `0` | The channel to play on, from 0 to 15. |
| `panning` | `int` | `-1` | Stereo position from 0 (left) to 127 (right); -1 uses the global panning. |
