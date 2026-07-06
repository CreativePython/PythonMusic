# setPitch()

Set the sequence's playback pitch, transposing the music to match.

## Parameters

Once an object `midisequence` has been created, you can use the following function:

```python
midisequence.setPitch(pitch)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int or float` | _required_ | The new playback pitch, as a MIDI pitch from 0 to 127. |
