# setPitch()

Set the sample's playback pitch, pitch-shifting it from its base pitch.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.setPitch(pitch)
```
```python
audiosample.setPitch(pitch, voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int or float` | _required_ | The new playback pitch, as a MIDI pitch from 0 to 127. |
| `voice` | `int` | `0` | Which voice to set, from 0 to one less than the number of voices. |
