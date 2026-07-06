# getFrameRate()

Return the sample's recording rate.

The rate is fixed by the audio file and is the same for every voice. To change how the sample sounds, use [setFrequency()](setFrequency.md) or [setPitch()](setPitch.md) instead.

## Parameters

Once an object `audiosample` has been created, you can use the following function:

```python
audiosample.getFrameRate()
```

## Returns

`return frameRate`

| Value | Type | Description |
|---|---|---|
| frameRate | `float` | The recording rate, in hertz, for example 44100.0; None if an error occurs. |
