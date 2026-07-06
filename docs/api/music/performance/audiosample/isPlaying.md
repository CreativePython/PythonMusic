# isPlaying()

Report whether the sample is currently playing.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.isPlaying()
```
```python
audiosample.isPlaying(voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `voice` | `int` | `0` | Which voice to check, from 0 to one less than the number of voices. |

## Returns

`return playing`

| Value | Type | Description |
|---|---|---|
| playing | `bool` | True if the sample is still playing, False otherwise; None if an error occurs. |
