# onInput()

Set up a function to call for a particular kind of MIDI event.

Call this again with different event types to handle each kind separately (one function per event type). Using ALL_EVENTS catches every event not already handled.

## Parameters

Once an object `midiin` has been created, you can use the following function:

```python
midiin.onInput(eventType, action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `eventType` | `int` | _required_ | The MIDI event type to handle, or ALL_EVENTS for anything not handled. |
| `action` | `function` | _required_ | The function to call; it receives four parameters: eventType, channel, data1, and data2. |
