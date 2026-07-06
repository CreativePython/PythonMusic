# audioOn()

Start a pitch sounding with an audio sample, and leave it sounding.

Stop it with [Play.audioOff()](audioOff.md).

## Parameters

`Play.audioOn()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.audioOn(pitch, audioSample)
```
```python
Play.audioOn(pitch, audioSample, velocity, panning, loopAudioSample, envelope)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int or float` | _required_ | A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0). |
| `audioSample` | `AudioSample` | _required_ | The audio sample to play the pitch with. |
| `velocity` | `int` | `127` | How loud the note is, from 0 to 127. |
| `panning` | `int` | `-1` | Stereo position from 0 (left) to 127 (right); -1 uses the global panning. |
| `loopAudioSample` | `bool` | `False` | Whether to loop the sample if it is shorter than the note. |
| `envelope` | `Envelope` | `None` | An envelope to shape the note's volume over time. |
