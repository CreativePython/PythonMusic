# selectMidiInput()

Connect to a preferred input MIDI device, or open a window to pick one.

If the named device is not available, a window opens listing the input devices found.

## Parameters

Once an object `midiin` has been created, you can use the following functions:

```python
midiin.selectMidiInput()
```
```python
midiin.selectMidiInput(preferredDevice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `preferredDevice` | `str` | `''` | The name of the input device to connect to. If omitted or unavailable, a selection window opens. |
