# setInstrument()

Set the instrument for a channel.

Notes played on this channel will sound using this instrument.

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.setInstrument(instrument)
```
```python
midiout.setInstrument(instrument, channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `instrument` | `int` | _required_ | The instrument (timbre), as a MIDI instrument number from 0 to 127. |
| `channel` | `int` | `0` | The channel to set, from 0 to 15. |
