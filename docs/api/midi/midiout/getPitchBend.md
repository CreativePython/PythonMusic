# getPitchBend()

Return the current pitch bend for a channel.

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.getPitchBend()
```
```python
midiout.getPitchBend(channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `int` | `0` | The channel to read, from 0 to 15. |

## Returns

`return pitchBend`

| Value | Type | Description |
|---|---|---|
| pitchBend | `int` | The current bend, in pitch bend units from -8191 to 8192, where 0 means no bend. |
