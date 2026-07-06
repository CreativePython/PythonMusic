# isPaused()

Report whether the sample is currently paused.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.isPaused()
```
```python
audiosample.isPaused(voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `voice` | `int` | `0` | Which voice to check, from 0 to one less than the number of voices. |

## Returns

`return paused`

| Value | Type | Description |
|---|---|---|
| paused | `bool` | True if the sample is paused, False otherwise; None if an error occurs. |
