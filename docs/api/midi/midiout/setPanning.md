# setPanning()

Set the main stereo position for a channel.

The default is the middle (64). Note that this does not affect a score played through [play()](play.md).

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.setPanning(panning)
```
```python
midiout.setPanning(panning, channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `panning` | `int` | _required_ | Stereo position from 0 (left) through 64 (center) to 127 (right). |
| `channel` | `int` | `0` | The channel to set, from 0 to 15. |
