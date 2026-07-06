# play()

Play the sample once.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.play()
```
```python
audiosample.play(start, size, voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `start` | `int or float` | `0` | Where to start playing, in milliseconds from the beginning of the sample. |
| `size` | `int` | `-1` | How much to play, in milliseconds; -1 plays to the end. |
| `voice` | `int` | `0` | Which voice to play on, from 0 to one less than the number of voices. |
