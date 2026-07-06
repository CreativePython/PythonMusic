# pause()

Pause the sample, remembering where it is.

Use [resume()](resume.md) to continue from this point.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.pause()
```
```python
audiosample.pause(voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `voice` | `int` | `0` | Which voice to pause, from 0 to one less than the number of voices. |
