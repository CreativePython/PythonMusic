# setVolume()

Set how loud the sample is.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.setVolume(volume)
```
```python
audiosample.setVolume(volume, delay, voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `volume` | `int` | _required_ | How loud to make the sample, from 0 to 127. |
| `delay` | `int or float` | `2` | How long to take making the change, in milliseconds. |
| `voice` | `int` | `0` | Which voice to set, from 0 to one less than the number of voices. |
