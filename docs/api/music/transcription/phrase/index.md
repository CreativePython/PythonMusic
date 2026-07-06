# Phrase

A Phrase object contains a sequence of [Note](../note/index.md) objects.  These notes are played sequentially (i.e., one after the other).  If a gap is desired between two notes, then a `REST` note should be introduced.  Phrases may also contain chords (i.e., sets of concurrent notes).

Phrases have start times.  If no start time is specified, then the phrase starts at the end of the previous phrase (or at the beginning of the piece, if this is the first phrase).

## Creating a Phrase

You can create a Phrase using the following functions:

```python
phrase = Phrase()
```

```python
phrase = Phrase(startTime)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `startTime` | `int or float` | `None` | A start time (0.0 is the beginning of the piece, 1.0 is a quarter note into the piece, etc.) |

For example,

```python
phrase = Phrase(5.0)
```

## Functions

Once a Phrase `phrase` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`addNote(note)`](addNote.md) | Add a note to the end of the phrase. |
| [`addNote(pitch, duration)`](addNote.md) | Add a new note with pitch and duration to the end of the phrase. |
| [`addNoteList(listOfPitches, listOfDurations)`](addNoteList.md) | Add many notes to the end of the phrase at once. |
| [`addChord(listOfPitches, duration)`](addChord.md) | Add a chord (several pitches sounded together) to the end of the phrase. |

You can also set the instrument, tempo, dynamic, panning, and title of the phrase.

| Function | Description |
|---|---|
| [`getInstrument()`](getInstrument.md) | Return the phrase's instrument. |
| [`setInstrument(instrument)`](setInstrument.md) | Set the phrase's instrument. |
| [`getTempo()`](getTempo.md) | Return the phrase's tempo. |
| [`setTempo(tempo)`](setTempo.md) | Set the phrase's tempo. |
| [`setDynamic(dynamic)`](setDynamic.md) | Set how loud every note in the phrase is. |
| [`setPan(pan)`](setPan.md) | Set the stereo position of every note in the phrase. |
| [`getTitle()`](getTitle.md) | Return the phrase's title. |
| [`setTitle(title)`](setTitle.md) | Set the phrase's title. |

**NOTE:** You may set the instrument on a single phrase. If you intend to add the phrase to a [Part](../part/index.md), then set the instrument at the Part level.  (If you do both, you may get unexpected results.)

Finally, here are some additional Phrase functions:

| Function | Description |
|---|---|
| [`copy()`](copy.md) | Return a copy of the phrase. |
| [`empty()`](empty.md) | Remove every note from the phrase. |
| [`getSize()`](getSize.md) | Return how many notes are in the phrase. |
| [`getNote(index)`](getNote.md) | Return the note at a given position, without changing the phrase. |
| [`getNoteList()`](getNoteList.md) | Return the phrase's notes. |
| [`getNoteStartTime(index)`](getNoteStartTime.md) | Return when the note at a given position starts. |
| [`getStartTime()`](getStartTime.md) | Return when the phrase starts. |
| [`setStartTime(startTime)`](setStartTime.md) | Set when the phrase starts. |
| [`getEndTime()`](getEndTime.md) | Return when the phrase ends. |
| [`removeNote(index)`](removeNote.md) | Remove the note at a given position from the phrase. |
| [`getHighestPitch()`](getHighestPitch.md) | Return the pitch of the highest note in the phrase. |
| [`getLowestPitch()`](getLowestPitch.md) | Return the pitch of the lowest note in the phrase. |
| [`getLongestDuration()`](getLongestDuration.md) | Return the duration of the longest note in the phrase. |
| [`getShortestDuration()`](getShortestDuration.md) | Return the duration of the shortest note in the phrase. |
