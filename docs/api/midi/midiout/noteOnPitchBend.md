# noteOnPitchBend()

Start a pitch sounding on the device with a pitch bend, and leave it sounding.

Stop it with [noteOff()](noteOff.md).

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.noteOnPitchBend(pitch)
```
```python
midiout.noteOnPitchBend(pitch, bend, dynamic, channel, panning)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int` | _required_ | A MIDI pitch, from 0 to 127. |
| `bend` | `int` | `0` | How far to bend the pitch, in pitch bend units from -8191 (full down) to 8192 (full up), where 0 means no bend. |
| `dynamic` | `int` | `100` | How loud the note is, from 0 to 127. |
| `channel` | `int` | `0` | The channel to play on, from 0 to 15. |
| `panning` | `int` | `-1` | Stereo position from 0 (left) to 127 (right); -1 uses the global panning. |
