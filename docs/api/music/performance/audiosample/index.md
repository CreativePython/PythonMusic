# AudioSample

AudioSample objects are used for playing external audio files. They can be played, pitch-shifted, looped, paused, resumed, and stopped, among other things.

An application may have several AudioSample objects playing at the same time. In fact, it is possible to create complex timbres by loading several simpler sound objects and manipulating them (e.g., change their frequency and/or volume) in real-time. AudioSample objects open endless timbral possibilities for interactive applications.

Also, see [Play.audio()](../../play/audio.md).

**NOTE:** One limitation is that AudioSamples are very expensive in terms of memory. Although it is possible to load whole songs, you should load only smaller files (e.g., a few seconds long). Since AudioSamples can be looped, one may load specially edited loops, and use them to create longer sound artifacts. For example, see [here](https://manual.audacityteam.org/man/creating_a_crossfade.html).

## Creating an AudioSample

You can create an AudioSample using the following functions:

```python
AudioSample(filename)
```

```python
AudioSample(filename, actualPitch, volume, voices)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `filename` | `str` | _required_ | The audio file to load (a WAV or AIF file). |
| `actualPitch` | `int or float` | `A4` | The recorded sound's own pitch, as a MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0). Defaults to A4 (440 Hz). |
| `volume` | `int` | `127` | How loud the sample is, from 0 to 127. |
| `voices` | `int` | `16` | How many voices can play at once, for polyphony. |

For example,

```python
sample = AudioSample("sound.wav")
```

where `"sound.wav"` is stored in the same folder as your program.

## Functions

Once an AudioSample `sample` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`play()`](play.md) | Play the sample once. |
| [`loop()`](loop.md) | Play the sample over and over. |
| [`stop()`](stop.md) | Stop the sample playing. |
| [`pause()`](pause.md) | Pause the sample, remembering where it is. |
| [`resume()`](resume.md) | Resume the sample from where it was paused. |
| [`isPlaying()`](isPlaying.md) | Report whether the sample is currently playing. |
| [`isPaused()`](isPaused.md) | Report whether the sample is currently paused. |
| [`getPitch()`](getPitch.md) | Return the sample's current playback pitch. |
| [`setPitch(pitch)`](setPitch.md) | Set the sample's playback pitch, pitch-shifting it from its base pitch. |
| [`getFrequency()`](getFrequency.md) | Return the sample's current playback frequency. |
| [`setFrequency(freq)`](setFrequency.md) | Set the sample's playback frequency, pitch-shifting it. |
| [`getPanning()`](getPanning.md) | Return the sample's stereo position. |
| [`setPanning(panning)`](setPanning.md) | Set the sample's stereo position. |
| [`getVolume()`](getVolume.md) | Return how loud the sample is. |
| [`setVolume(volume)`](setVolume.md) | Set how loud the sample is. |
| [`getFrameRate()`](getFrameRate.md) | Return the sample's recording rate. |

**NOTE:** All the above functions have an optional parameter, voice – to indicate a particular voice, if desired. For most practical situations this is not necessary to use.
