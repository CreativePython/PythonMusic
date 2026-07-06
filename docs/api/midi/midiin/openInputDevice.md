# openInputDevice()

Open a named input MIDI device.

This is the callback used by the device-selection window; you do not normally call it yourself.

## Parameters

Once an object `midiin` has been created, you can use the following function:

```python
midiin.openInputDevice(selectedItem)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `selectedItem` | `str` | _required_ | The name of the input device to open. |
