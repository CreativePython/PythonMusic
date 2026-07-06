# performAttackDelaySustain()

Apply the envelope's attack, delay, and sustain to a voice of an audio sample.

This starts the volume changes that shape the beginning of the sound. Usually called for you by Play.audioOn().

## Parameters

Once an object `envelope` has been created, you can use the following function:

```python
envelope.performAttackDelaySustain(audioSample, volume, voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `audioSample` | `AudioSample` | _required_ | The audio sample to shape. |
| `volume` | `int` | _required_ | The note's overall volume, from 0 to 127, that the envelope's levels are taken relative to. |
| `voice` | `int` | _required_ | Which voice of the audio sample to shape. |
