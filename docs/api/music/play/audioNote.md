# audioNote()

Schedule a note to play with an audio sample, after a delay and lasting a set time.

## Parameters

`Play.audioNote()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.audioNote(pitch, start, duration, audioSample)
```
```python
Play.audioNote(pitch, start, duration, audioSample, velocity, panning, loopAudioSample, envelope)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int or float` | _required_ | A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0). |
| `start` | `int or float` | _required_ | How long from now the note begins, in milliseconds. |
| `duration` | `int or float` | _required_ | How long the note lasts, in milliseconds. |
| `audioSample` | `AudioSample` | _required_ | The audio sample to play the note with. |
| `velocity` | `int` | `127` | How loud the note is, from 0 to 127. |
| `panning` | `int` | `-1` | Stereo position from 0 (left) to 127 (right); -1 uses the global panning. |
| `loopAudioSample` | `bool` | `False` | Whether to loop the sample if the note outlasts it. |
| `envelope` | `Envelope` | `None` | An envelope to shape the note's volume over time. |
