# noteOn()

Start a pitch sounding on the device, and leave it sounding.

The note keeps playing until you stop it with [noteOff()](noteOff.md).

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.noteOn(pitch)
```
```python
midiout.noteOn(pitch, dynamic, channel, panning)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int or float` | _required_ | A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0) to reach pitches between the standard notes. |
| `dynamic` | `int` | `100` | How loud the note is, from 0 to 127. |
| `channel` | `int` | `0` | The channel to play on, from 0 to 15. |
| `panning` | `int` | `-1` | Stereo position from 0 (left) to 127 (right); -1 uses the global panning. |
