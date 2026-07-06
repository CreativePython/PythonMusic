# setVolume()

Set the main volume for a channel.

This is the channel's overall volume, separate from how loud each note is played
(see [Play.noteOn()](noteOn.md)).

## Parameters

`Play.setVolume()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.setVolume(volume)
```
```python
Play.setVolume(volume, channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `volume` | `int` | _required_ | The main volume, from 0 to 127. |
| `channel` | `int` | `0` | The channel to set, from 0 to 15. |
