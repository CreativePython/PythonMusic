# Play

The Play functions use a MIDI synthesizer to play musical material. The first function, [Play.midi()](midi.md), is used to render musical compositions stored in [Note](../transcription/note/index.md), [Phrase](../transcription/phrase/index.md), [Part](../transcription/part/index.md), and [Score](../transcription/score/index.md) objects. The other Play functions are more advanced, as they are intended for building interactive musical instruments and installations.

## Creating a Play

Play is a static utility; you don't instantiate it like other objects.  Call its methods on the class itself.  For example,

```python
Play.midi(score)
```

## Functions

The following Play functions are always available:

### Playing MIDI Material

| Function | Description |
|---|---|
| [`midi(material)`](midi.md) | Play music library material through the synthesizer. |
| [`stop()`](stop.md) | Stop all music started through Play from sounding. |
| [`note(pitch, start, duration)`](note.md) | Schedule a note to play after a delay and last a set time. |
| [`noteOn(pitch)`](noteOn.md) | Start a pitch sounding, and leave it sounding. |
| [`noteOnPitchBend(pitch)`](noteOnPitchBend.md) | Start a pitch sounding with a pitch bend, and leave it sounding. |
| [`noteOff(pitch)`](noteOff.md) | Stop a pitch from sounding. |
| [`allNotesOff()`](allNotesOff.md) | Stop every note from sounding, on all channels. |
| [`frequency(frequency, start, duration)`](frequency.md) | Schedule a frequency to play after a delay and last a set time. |
| [`frequencyOn(frequency)`](frequencyOn.md) | Start a frequency sounding, and leave it sounding. |
| [`frequencyOff(frequency)`](frequencyOff.md) | Stop a frequency from sounding. |
| [`allFrequenciesOff()`](allFrequenciesOff.md) | Stop every frequency from sounding, on all channels. |
| [`setPitchBend()`](setPitchBend.md) | Set the pitch bend for a channel, used for notes played next. |
| [`getPitchBend()`](getPitchBend.md) | Return the current pitch bend for a channel. |
| [`setInstrument(instrument)`](setInstrument.md) | Set the instrument for a channel. |
| [`getInstrument()`](getInstrument.md) | Return the instrument set for a channel. |
| [`setVolume(volume)`](setVolume.md) | Set the main volume for a channel. |
| [`getVolume()`](getVolume.md) | Return the main volume for a channel. |
| [`setPanning(panning)`](setPanning.md) | Set the main stereo position for a channel. |
| [`getPanning()`](getPanning.md) | Return the main stereo position for a channel. |
| [`getSoundfont()`](getSoundfont.md) | Return the path of the soundfont currently used for playback. |
| [`setSoundfont(soundfont)`](setSoundfont.md) | Set the soundfont used for playback. |

### Playing Musical Material with AudioSamples

| Function | Description |
|---|---|
| [`audio(material, audioSamples)`](audio.md) | Play music library material using audio samples as the instruments. |
| [`audioNote(pitch, start, duration, audioSample)`](audioNote.md) | Schedule a note to play with an audio sample, after a delay and lasting a set time. |
| [`audioOn(pitch, audioSample)`](audioOn.md) | Start a pitch sounding with an audio sample, and leave it sounding. |
| [`audioOff(pitch, audioSample)`](audioOff.md) | Stop a pitch from sounding on an audio sample. |
| [`allAudioNotesOff()`](allAudioNotesOff.md) | Stop every note from sounding on all audio samples. |

### Running Code with Musical Material

| Function | Description |
|---|---|
| [`code(material, actions)`](code.md) | Run your own functions in time with music library material. |
