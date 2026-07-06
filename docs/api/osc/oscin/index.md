# OscIn

Receive OSC messages from another device.

OSC (Open Sound Control) is a way for programs and devices to send each other messages over a network. Creating an OscIn listens for messages on a port; use [onInput()](onInput.md) to call your own function whenever a message arrives at a given address.

When an OSC message arrives, any function registered for this message will be called and given the [OscMessage](../oscmessage/index.md) as an argument.

## Creating an OscIn

You can create an OscIn using the following functions:

```python
OscIn()
```

```python
OscIn(port)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `port` | `int` | `57110` | The port to listen on, a number from 1024 to 65535 that no other program is using. |

For example,

```python title="oscIn1.py"
--8<-- "examples/_snippets/oscIn1.py"
```

## Functions

Once an OscIn `oscin` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`onInput(oscAddress, action)`](onInput.md) | Set up a function to call when a message arrives at a given address. |
| [`showMessages()`](showMessages.md) | Start printing incoming OSC messages to the console. |
| [`hideMessages()`](hideMessages.md) | Stop printing incoming OSC messages to the console. |
