# MidiOut

Send MIDI messages to an output device or synthesizer.

Creating a MidiOut connects to an output MIDI device to generate sounds from MIDI messages. If you do not name a device, or the named device is unavailable, a window opens for you to pick from the devices found. Once connected, you can play music library material, start and stop individual notes and frequencies, and set each channel's instrument, volume, and panning.

## Creating a MidiOut

You can create a MidiOut using the following functions:

```python
MidiOut()
```

```python
MidiOut(preferredDevice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `preferredDevice` | `str` | `''` | The name of the output device to connect to. If omitted or unavailable, a selection window opens. |

For example,

```python
midiout = MidiOut()
```

creates a MidiOut object called *midiout*. When executed, a display will open up to select an ouput MIDI device.

MidiOut objects may also be created with a specific device in mind.  For example,

```python
midiout = MidiOut("M-Audio USB Uno MIDI Interface")
```

creates a connection to an output device directly (i.e., no selection display is shown – faster, if you already know the name of the device).

## Functions

Once *midiout* has been created, the following functions are available:

### Playing Musical Material

The first function, [midiout.play()](play.md), is used to play musical material stored in [Note](../../music/transcription/note/index.md), [Phrase](../../music/transcription/phrase/index.md), [Part](../../music/transcription/part/index.md), and [Score](../../music/transcription/score/index.md) objects via the external device.

| Function | Description |
|---|---|
| [`play(material)`](play.md) | Play music library material through the output device. |

### Playing Musical Notes Interactively

This functionality can be used to perform live, or to build interactive musical instruments.

| Function | Description |
|---|---|
| [`noteOn(pitch)`](noteOn.md) | Start a pitch sounding on the device, and leave it sounding. |
| [`noteOnPitchBend(pitch)`](noteOnPitchBend.md) | Start a pitch sounding on the device with a pitch bend, and leave it sounding. |
| [`noteOff(pitch)`](noteOff.md) | Stop a pitch from sounding on the device. |
| [`note(pitch, start, duration)`](note.md) | Schedule a note on the device to play after a delay and last a set time. |
| [`allNotesOff()`](allNotesOff.md) | Stop every note from sounding, on all channels. |

You can also make global changes interactively on instrument, volume, panning, and pitch bend.

| Function | Description |
|---|---|
| [`getInstrument()`](getInstrument.md) | Return the instrument set for a channel. |
| [`setInstrument(instrument)`](setInstrument.md) | Set the instrument for a channel. |
| [`getVolume()`](getVolume.md) | Return the main volume for a channel. |
| [`setVolume(volume)`](setVolume.md) | Set the main volume for a channel. |
| [`getPanning()`](getPanning.md) | Return the main stereo position for a channel. |
| [`setPanning(panning)`](setPanning.md) | Set the main stereo position for a channel. |
| [`getPitchBend()`](getPitchBend.md) | Return the current pitch bend for a channel. |
| [`setPitchBend()`](setPitchBend.md) | Set the pitch bend for a channel, used for notes played next. |

### Playing Microtonal Material

To play microtonal material, simply create [Note](../../music/transcription/note/index.md) objects using **float** (e.g., 443.1) pitches.  Then, you may store them in [Phrase](../../music/transcription/phrase/index.md), [Part](../../music/transcription/part/index.md), or [Score](../../music/transcription/score/index.md) objects and [play](#playing-musical-material) them normally.

| Function | Description |
|---|---|
| [`frequencyOn(frequency)`](frequencyOn.md) | Start a frequency sounding on the device, and leave it sounding. |
| [`frequencyOff(frequency)`](frequencyOff.md) | Stop a frequency from sounding on the device. |
| [`frequency(frequency, start, duration)`](frequency.md) | Schedule a frequency on the device to play after a delay and last a set time. |
| [`allFrequenciesOff()`](allFrequenciesOff.md) | Stop every frequency from sounding, on all channels. |

**WARNING:** For polyphony (to play concurrent microtonal notes), you must play notes on different MIDI channels.

The MIDI standard does not support microtones. Microtones are rendered here using MIDI pitch bend. Since there is only one pitch bend per channel, you must spread concurrent notes across channels. (Also, remember that channel 9 is special – percussion only.)

### Send Arbitrary MIDI Messages

You can send arbitrary MIDI messages (e.g., CC – control change, etc.) to an external device.

| Function | Description |
|---|---|
| [`sendMidiMessage(eventType, channel, data1, data2)`](sendMidiMessage.md) | Send a raw MIDI message to the device. |

**WARNING:** If you use an automated MIDI learn feature in your external program (or device) to connect MIDI messages sent from PEM to arbitrary functionality, **do NOT press PEM's stop button**, while your program is in learn mode.

When PEM's stop button is pressed, it sends an ALL-NOTES-OFF message (i.e., CC 123 message to all channels). This is done to turn off all sounds generated by equipment connected to PEM (as one might expect).

If your external program is in MIDI learn more, **first turn MIDI learning off, **and** then press the PEM stop button**. Otherwise, your program will also learn the ALL_NOTES_OFF message (which is something you probably don’t want).

### Manage Output Devices

You can connect and disconnect from MIDI devices after a MidiOut has been created.

| Function | Description |
|---|---|
| [`stop()`](stop.md) | Stop all MIDI music on the device from sounding. |
| [`selectMidiOutput()`](selectMidiOutput.md) | Connect to a preferred output MIDI device, or open a window to pick one. |
| [`openOutputDevice(selectedItem)`](openOutputDevice.md) | Open a named output MIDI device. |
| [`close()`](close.md) | Close the output device. |
