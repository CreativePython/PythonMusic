# openOutputDevice()

Open a named output MIDI device.

This is the callback used by the device-selection window; you do not normally call it yourself.

## Parameters

Once an object `midiout` has been created, you can use the following function:

```python
midiout.openOutputDevice(selectedItem)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `selectedItem` | `str` | _required_ | The name of the output device to open. |
