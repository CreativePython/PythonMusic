# onInput()

Set up a function to call when a message arrives at a given address.

An OSC address looks like a URL, for example "/first/second/third". The address may also be a pattern, to match several addresses at once.

## Parameters

Once an object `oscin` has been created, you can use the following function:

```python
oscin.onInput(oscAddress, action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `oscAddress` | `str` | _required_ | The OSC address to listen for, for example "/first/second/third". |
| `action` | `function` | _required_ | The function to call; it receives one parameter, the incoming OscMessage. |
