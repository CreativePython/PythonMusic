# MidiSequence

Play MIDI music, with live control over pitch, tempo, and volume.

The MidiSequence class includes functions related to playing external MIDI files (as well as Part and Score objects) in real-time. A MIDI sequence provides playback features that are similar to the functionality for [AudioSamples](../audiosample/index.md). Again, these functions are intended for building interactive musical instruments and installations.

## Creating a MidiSequence

You can create a MidiSequence using the following functions:

```python
MidiSequence(material)
```

```python
MidiSequence(material, pitch, volume)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `str, Note, Phrase, Part, or Score` | _required_ | The music to play, or the filename of a MIDI file (.mid). |
| `pitch` | `int or float` | `A4` | The pitch to play at, as a MIDI pitch. Defaults to A4. |
| `volume` | `int` | `127` | How loud to play, from 0 to 127. |

For example,

```python
sequence = MidiSequence("song.mid")
```

## Functions

Once a MidiSequence `sequence` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`play()`](play.md) | Play the sequence once. |
| [`loop()`](loop.md) | Play the sequence over and over, forever. |
| [`stop()`](stop.md) | Stop the sequence playing. |
| [`pause()`](pause.md) | Pause the sequence, remembering where it is. |
| [`resume()`](resume.md) | Resume the sequence from where it was paused. |
| [`isPlaying()`](isPlaying.md) | Report whether the sequence is currently playing. |
| [`getPitch()`](getPitch.md) | Return the sequence's current playback pitch. |
| [`setPitch(pitch)`](setPitch.md) | Set the sequence's playback pitch, transposing the music to match. |
| [`getDefaultPitch()`](getDefaultPitch.md) | Return the pitch the sequence was created with. |
| [`getVolume()`](getVolume.md) | Return the sequence's current playback volume. |
| [`setVolume(volume)`](setVolume.md) | Set the sequence's playback volume, making it louder or softer. |
| [`getTempo()`](getTempo.md) | Return the sequence's current playback tempo. |
| [`setTempo(bpm)`](setTempo.md) | Set the sequence's playback tempo. |
| [`getDefaultTempo()`](getDefaultTempo.md) | Return the tempo the sequence was created with. |
