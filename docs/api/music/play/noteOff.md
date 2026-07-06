# noteOff()

Stop a pitch from sounding.

If the pitch is not sounding on this channel, nothing happens.

## Parameters

`Play.noteOff()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.noteOff(pitch)
```
```python
Play.noteOff(pitch, channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int or float` | _required_ | A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0). |
| `channel` | `int` | `0` | The channel it is playing on, from 0 to 15. |
