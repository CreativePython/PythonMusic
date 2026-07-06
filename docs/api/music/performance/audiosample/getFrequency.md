# getFrequency()

Return the sample's current playback frequency.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.getFrequency()
```
```python
audiosample.getFrequency(voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `voice` | `int` | `0` | Which voice to read, from 0 to one less than the number of voices. |

## Returns

`return frequency`

| Value | Type | Description |
|---|---|---|
| frequency | `float` | The current playback frequency, in hertz (8.17 to 12600.0); None if an error occurs. |
