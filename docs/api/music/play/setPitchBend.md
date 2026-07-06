# setPitchBend()

Set the pitch bend for a channel, used for notes played next.

## Parameters

`Play.setPitchBend()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.setPitchBend()
```
```python
Play.setPitchBend(bend, channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bend` | `int` | `0` | How far to bend the pitch, in pitch bend units from -8191 (full down) to 8192 (full up), where 0 means no bend. |
| `channel` | `int` | `0` | The channel to set, from 0 to 15. |
