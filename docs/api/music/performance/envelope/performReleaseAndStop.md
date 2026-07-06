# performReleaseAndStop()

Apply the envelope's release (fade-out) to a voice of an audio sample, then stop it.

Usually called for you by Play.audioOff().

## Parameters

Once an object `envelope` has been created, you can use the following function:

```python
envelope.performReleaseAndStop(audioSample, voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `audioSample` | `AudioSample` | _required_ | The audio sample to fade out and stop. |
| `voice` | `int` | _required_ | Which voice of the audio sample to fade out and stop. |
