# getInstrument()

Return the instrument set for a channel.

## Parameters

`Play.getInstrument()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.getInstrument()
```
```python
Play.getInstrument(channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `int` | `0` | The channel to read, from 0 to 15. |

## Returns

`return instrument`

| Value | Type | Description |
|---|---|---|
| instrument | `int` | The instrument (timbre), as a MIDI instrument number from 0 to 127. |
