# getVolume()

Return the sequence's current playback volume.

## Parameters

Once an object `midisequence` has been created, you can use the following function:

```python
midisequence.getVolume()
```

## Returns

`return volume`

| Value | Type | Description |
|---|---|---|
| volume | `int` | The current volume, from 0 (silent) to 127 (loudest). |