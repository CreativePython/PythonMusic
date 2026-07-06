# sendMessage()

Send an OSC message to the connected device.

A message is an address plus any number of arguments.

## Parameters

Once an object `iannixout` has been created, you can use the following function:

```python
iannixout.sendMessage(oscAddress, *args)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `oscAddress` | `str` | _required_ | The OSC address to send to, for example "/first/second/third". |
| `*args` | `int, float, str, or bool` | _optional_ | Zero or more values to send along with the message. |
