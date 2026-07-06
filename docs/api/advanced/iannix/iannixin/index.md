# IannixIn

IanniX is a graphic sequencer. As its score plays, IanniX sends out OSC messages for the triggers and cursors in the score, and for its transport controls (play, stop, and fast rewind). Create an IannixIn to listen on a port, then use the on... methods to run your own functions when those messages arrive.

## Creating a IannixIn

You can create a IannixIn using the following functions:

```python
IannixIn()
```

```python
IannixIn(port)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `port` | `int` | `57110` | The port to listen on for messages from IanniX. |

For example,

```python
iannixin = IannixIn(57800)
```

## Functions

Once a IannixIn `iannixin` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`onTrigger(triggerID, action)`](onTrigger.md) | Set up a function to call when a given trigger fires in the IanniX score. |
| [`onCursor(cursorID, action)`](onCursor.md) | Set up a function to call as a given cursor moves through the IanniX score. |
| [`onPlay(action)`](onPlay.md) | Set up a function to call when IanniX starts playing. |
| [`onStop(action)`](onStop.md) | Set up a function to call when IanniX stops. |
| [`onFastRewind(action)`](onFastRewind.md) | Set up a function to call when IanniX fast-rewinds. |
| [`onInput(oscAddress, action)`](onInput.md) | Set up a function to call when a message arrives at a given address. |
| [`showMessages()`](showMessages.md) | Start printing incoming OSC messages to the console. |
| [`hideMessages()`](hideMessages.md) | Stop printing incoming OSC messages to the console. |
