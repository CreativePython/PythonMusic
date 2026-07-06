# setVolume()

Set the main volume for a channel.

This is the channel's overall volume, separate from how loud each note is played (see [noteOn()](noteOn.md)).

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.setVolume(volume)
```
```python
midiout.setVolume(volume, channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `volume` | `int` | _required_ | The main volume, from 0 to 127. |
| `channel` | `int` | `0` | The channel to set, from 0 to 15. |
