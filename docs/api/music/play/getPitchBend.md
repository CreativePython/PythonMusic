# getPitchBend()

Return the current pitch bend for a channel.

## Parameters

`Play.getPitchBend()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.getPitchBend()
```
```python
Play.getPitchBend(channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `int` | `0` | The channel to read, from 0 to 15. |

## Returns

`return pitchBend`

| Value | Type | Description |
|---|---|---|
| pitchBend | `int` | The current bend, in pitch bend units from -8191 to 8192, where 0 means no bend. |
