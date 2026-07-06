# addChord()

Add a chord (several pitches sounded together) to the end of the phrase.

## Parameters

Once an object `phrase` has been created, you can use the following functions:

```python
phrase.addChord(listOfPitches, duration)
```
```python
phrase.addChord(listOfPitches, duration, dynamic, pan, length)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `listOfPitches` | `list[int]` | _required_ | The chord's pitches, each a MIDI pitch from 0 to 127. |
| `duration` | `int or float` | _required_ | How long the chord lasts, as a float where 1.0 is a quarter note. |
| `dynamic` | `int` | `85` | How loud the chord is, from 0 to 127. |
| `pan` | `int or float` | `0.5` | The stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right). |
| `length` | `int or float` | `None` | How long the chord actually sounds, in the same units as duration. Defaults to 90% of the duration. |
