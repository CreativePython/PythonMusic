# OscMessage

Hold an OSC message: an address and its arguments.

An OscMessage is what the function you set up with [OscIn.onInput()](../oscin/onInput.md) receives. Read the message with [getAddress()](getAddress.md) and [getArguments()](getArguments.md).

## Creating an OscMessage

You normally receive an OscMessage, rather than create one.  To send an OSC message, use [OscOut.sendMessage()](../oscout/sendMessage.md), which builds and sends an OscMessage object for you.

If necessary, you can create an OscMessage using the following functions:

```python
 OscMessage(oscAddress)
```

```python
OscMessage(oscAddress, arguments)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `oscAddress` | `str` | _required_ | The OSC address, for example "/first/second/third". |
| `arguments` | `list` | `None` | The message's arguments (numbers, text, or True/False). Defaults to no arguments. |

For example,

```python title="oscIn2.py"
--8<-- "examples/_snippets/oscIn2.py"
```

## Functions

Once an OscMessage `message` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getAddress()`](getAddress.md) | Return the message's OSC address. |
| [`getArguments()`](getArguments.md) | Return the message's arguments. |
