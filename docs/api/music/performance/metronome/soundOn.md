# soundOn()

Play a sound on every metronome tick.

The strong (first) beat of each measure sounds at the given volume; the other beats sound softer (about 70% as loud).

## Parameters

Once an object `metronome` has been created, you can use the following functions:

```python
metronome.soundOn()
```
```python
metronome.soundOn(pitch, volume, channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pitch` | `int` | `ACOUSTIC_BASS_DRUM` | The pitch to play on each tick, as a MIDI pitch. |
| `volume` | `int` | `127` | How loud the strong beat is, from 0 to 127. |
| `channel` | `int` | `9` | The channel to play on, from 0 to 15; channel 9 is the percussion channel. |
