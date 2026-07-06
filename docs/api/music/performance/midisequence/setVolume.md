# setVolume()

Set the sequence's playback volume, making it louder or softer.

## Parameters

Once an object `midisequence` has been created, you can use the following function:

```python
midisequence.setVolume(volume)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `volume` | `int` | _required_ | The new volume, from 0 (silent) to 127 (loudest). |