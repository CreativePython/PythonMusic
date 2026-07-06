# setFrequency()

Set the sample's playback frequency, pitch-shifting it.

Like [setPitch()](setPitch.md), but finer. This lets the sound land between the standard pitches. For example, frequency 440 Hz is the same as pitch A4.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.setFrequency(freq)
```
```python
audiosample.setFrequency(freq, voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `freq` | `int or float` | _required_ | The new playback frequency, in hertz (8.17 to 12600.0). |
| `voice` | `int` | `0` | Which voice to set, from 0 to one less than the number of voices. |
