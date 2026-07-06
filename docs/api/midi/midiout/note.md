# note()

Schedule a note on the device to play after a delay and last a set time.

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.note(pitch, start, duration)
```
```python
midiout.note(pitch, start, duration, dynamic, channel, panning)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int` | _required_ | A MIDI pitch, from 0 to 127. |
| `start` | `int or float` | _required_ | How long from now the note begins, in milliseconds. |
| `duration` | `int or float` | _required_ | How long the note lasts, in milliseconds. |
| `dynamic` | `int` | `100` | How loud the note is, from 0 to 127. |
| `channel` | `int` | `0` | The channel to play on, from 0 to 15. |
| `panning` | `int` | `-1` | Stereo position from 0 (left) to 127 (right); -1 uses the global panning. |
