# sendMidiMessage()

Send a raw MIDI message to the device.

For messages the other methods do not cover. See the MIDI standard, or your synthesizer's documentation, for the meaning of each value.

## Parameters

Once an object `midiout` has been created, you can use the following function:

```python
midiout.sendMidiMessage(eventType, channel, data1, data2)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `eventType` | `int` | _required_ | The MIDI event type. |
| `channel` | `int` | _required_ | The MIDI channel, from 0 to 15. |
| `data1` | `int` | _required_ | The first data byte; its meaning depends on the event type. |
| `data2` | `int` | _required_ | The second data byte; its meaning depends on the event type. |
