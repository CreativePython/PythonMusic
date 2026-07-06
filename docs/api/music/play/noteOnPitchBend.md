# noteOnPitchBend()

Start a pitch sounding with a pitch bend, and leave it sounding.

Stop it with [Play.noteOff()](noteOff.md).

## Parameters

`Play.noteOnPitchBend()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.noteOnPitchBend(pitch)
```
```python
Play.noteOnPitchBend(pitch, bend, velocity, channel, panning)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int` | _required_ | A MIDI pitch, from 0 to 127. |
| `bend` | `int` | `0` | How far to bend the pitch, in pitch bend units from -8191 (full down) to 8192 (full up), where 0 means no bend. |
| `velocity` | `int` | `100` | How loud the note is, from 0 to 127. |
| `channel` | `int` | `0` | The channel to play on, from 0 to 15. |
| `panning` | `int` | `-1` | Stereo position from 0 (left) to 127 (right); -1 uses the global panning. |
