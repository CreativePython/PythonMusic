# getInstrument()

Return the instrument set for a channel.

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.getInstrument()
```
```python
midiout.getInstrument(channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `int` | `0` | The channel to read, from 0 to 15. |

## Returns

`return instrument`

| Value | Type | Description |
|---|---|---|
| instrument | `int` | The instrument (timbre), as a MIDI instrument number from 0 to 127. |
