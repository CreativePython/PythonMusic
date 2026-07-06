# Note

Notes contain the simplest possible musical events, consisting of pitch, duration, etc.

The pitch can be a MIDI pitch or a frequency in hertz (8.17 to 12600.0). Pass `REST` for the value to make a silent note (a rest).  When you create a note, you can also set the dynamic (volume), pan (stereo position), or length (sound duration).

## Creating a Note

You can create a Note using the following functions:

```python
Note(value, duration)
```

```python
Note(value, duration, dynamic, pan, length)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `value` | `int or float` | _required_ | A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0) to reach pitches between the standard notes. Use REST for a rest. |
| `duration` | `int or float` | _required_ | How long the note lasts in the written score, as a float where 1.0 is a quarter note. |
| `dynamic` | `int` | `85` | How loud the note is, from 0 to 127. |
| `pan` | `int or float` | `0.5` | The stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right). |
| `length` | `int or float` | `None` | How long the note actually sounds, in the same units as duration. Defaults to 90% of the duration, so notes sound distinct. |

For example,

```python
note = Note(A4, HN)
```

## Functions

Once a Note `note` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getPitch()`](getPitch.md) | Return the note's pitch. |
| [`getDuration()`](getDuration.md) | Return how long the note lasts in the written score. |
| [`getDynamic()`](getDynamic.md) | Return how loud the note is. |
| [`getPan()`](getPan.md) | Return the note's stereo position. |
| [`getLength()`](getLength.md) | Return how long the note actually sounds. |
| [`setPitch(pitch)`](setPitch.md) | Set the note's pitch. |
| [`setDuration(duration)`](setDuration.md) | Set how long the note lasts in the written score. |
| [`setDynamic(dynamic)`](setDynamic.md) | Set how loud the note is. |
| [`setPan(pan)`](setPan.md) | Set the note's stereo position. |
| [`setLength(length)`](setLength.md) | Set how long the note actually sounds. |
| [`isRest()`](isRest.md) | Report whether the note is a rest. |
| [`copy()`](copy.md) | Return a copy of the note. |

When working with frequencies, the following functions may also be used:

| Function | Description |
|---|---|
| [`getFrequency()`](getFrequency.md) | Return the note's pitch as a frequency. |
| [`setFrequency(frequency)`](setFrequency.md) | Set the note's pitch from a frequency. |
| [`getPitchBend()`](getPitchBend.md) | Return the note's pitch bend, the gap between its pitch and its exact frequency. |
