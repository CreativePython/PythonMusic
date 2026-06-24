# onClose()

Register a function to call right before the display closes.

Called whether the display is closed with the mouse, the keyboard, or [close()](../../../display/close.md). Use it to clean up, play a sound, update other displays, and so on.

## Parameters

Once an object `display` has been created, you can use the following function:

```python
display.onClose(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call; it receives no parameters. |
