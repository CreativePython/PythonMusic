# addNoteList()

Add many notes to the end of the phrase at once.

The lists are parallel: the first note takes the first pitch, the first duration, and so on. A pitch may itself be a list, which adds a chord. The dynamic, panning, and length lists are optional.

## Parameters

Once an object `phrase` has been created, you can use the following functions:

```python
phrase.addNoteList(listOfPitches, listOfDurations)
```
```python
phrase.addNoteList(listOfPitches, listOfDurations, listOfDynamics, listOfPannings, listOfLengths)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `listOfPitches` | `list[int or list[int]]` | _required_ | The notes' pitches, each a MIDI pitch (or a list of pitches for a chord). |
| `listOfDurations` | `list[int or float]` | _required_ | The notes' durations, each a float where 1.0 is a quarter note. |
| `listOfDynamics` | `list[int]` | `[]` | The notes' dynamics, each from 0 to 127. Defaults to full for every note. |
| `listOfPannings` | `list[int or float]` | `[]` | The notes' stereo positions, each from 0.0 (left) to 1.0 (right). Defaults to center. |
| `listOfLengths` | `list[int or float]` | `[]` | The notes' sounding lengths. Defaults to 90% of each duration. |
