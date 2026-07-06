# getPanning()

Return the main stereo position for a channel.

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.getPanning()
```
```python
midiout.getPanning(channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `int` | `0` | The channel to read, from 0 to 15. |

## Returns

`return panning`

| Value | Type | Description |
|---|---|---|
| panning | `int` | Stereo position from 0 (left) through 64 (center) to 127 (right). |
