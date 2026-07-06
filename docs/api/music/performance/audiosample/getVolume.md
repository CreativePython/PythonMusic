# getVolume()

Return how loud the sample is.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.getVolume()
```
```python
audiosample.getVolume(voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `voice` | `int` | `0` | Which voice to read, from 0 to one less than the number of voices. |

## Returns

`return volume`

| Value | Type | Description |
|---|---|---|
| volume | `int` | How loud the sample is, from 0 to 127; None if an error occurs. |
