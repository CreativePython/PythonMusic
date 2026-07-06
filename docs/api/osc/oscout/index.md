# OscOut

Send OSC messages to another device.

OSC (Open Sound Control) is a way for programs and devices to send each other messages over a network. Creating an OscOut connects to a device at an IP address and port; use [sendMessage()](sendMessage.md) to send it messages. You can make several OscOut objects to reach several devices.

## Creating an OscOut

You can create an OscOut using the following functions:

```python
OscOut()
```
```python
OscOut(ipAddress, port)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ipAddress` | `str` | `'localhost'` | The device's IP address, for example "192.168.1.223". Use "localhost" for a program on this same computer. |
| `port` | `int` | `57110` | The port the device is listening on, a number from 1024 to 65535. |

For example,

```python
oscout = OscOut("192.168.1.223", 57110)
```

## Functions

Once an OscOut `oscout` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`sendMessage(oscAddress)`](sendMessage.md) | Send an OSC message to the connected device. |
