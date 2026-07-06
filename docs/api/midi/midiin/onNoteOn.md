# onNoteOn()

Set up a function to call whenever a note is played on the device.

## Parameters

Once an object `midiin` has been created, you can use the following function:

```python
midiin.onNoteOn(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call; it receives four parameters: eventType (144), channel (0 to 15), data1 (the pitch, 0 to 127), and data2 (the velocity, 0 to 127). |
