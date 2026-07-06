# onSetInstrument()

Set up a function to call whenever the instrument is changed on the device.

## Parameters

Once an object `midiin` has been created, you can use the following function:

```python
midiin.onSetInstrument(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call; it receives four parameters: eventType (192), channel (0 to 15), data1 (the new instrument, 0 to 127), and data2 (unused). |
