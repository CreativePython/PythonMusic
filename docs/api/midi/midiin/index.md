# MidiIn

Receive MIDI messages from an input device, such as a keyboard or controller.

Creating a MidiIn connects to an input MIDI device. If you do not name one, or the named one is unavailable, a window opens for you to pick from the devices found. Once connected, use the on… methods to run your own functions when notes are played, released, or the instrument is changed.

## Creating a MidiIn

You can create a MidiIn using the following functions:

```python
MidiIn()
```

```python
MidiIn(preferredDevice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `preferredDevice` | `str` | `''` | The name of the input device to connect to. If omitted or unavailable, a selection window opens. |

For example,

```python
midiin = MidiIn()
```

creates a MidiIn object called *midiin*.  When executed, a display will open up to select an input MIDI device.

MidiIn objects may also be created with a specific device in mind. For example,

```python
m = MidiIn("AKAI MPKmini2")
```

creates a connection to an AKAI MPKmini2 MIDI controller directly (i.e., no selection display is shown – faster, if you already know the name of the device).

## Functions

Once *midiin* has been created, the following functions are available:

| Function | Description |
|---|---|
| [`onNoteOn(action)`](onNoteOn.md) | Set up a function to call whenever a note is played on the device. |
| [`onNoteOff(action)`](onNoteOff.md) | Set up a function to call whenever a note is released on the device. |
| [`onSetInstrument(action)`](onSetInstrument.md) | Set up a function to call whenever the instrument is changed on the device. |
| [`onInput(eventType, action)`](onInput.md) | Set up a function to call for a particular kind of MIDI event. |
| [`showMessages()`](showMessages.md) | Start printing incoming MIDI messages to the console. |
| [`hideMessages()`](hideMessages.md) | Stop printing incoming MIDI messages to the console. |
| [`selectMidiInput()`](selectMidiInput.md) | Connect to a preferred input MIDI device, or open a window to pick one. |
| [`openInputDevice(selectedItem)`](openInputDevice.md) | Open a named input MIDI device. |
| [`close()`](close.md) | Close the input device and free its resources. |
