# Mod

The Mod class contains many functions for modifying, or varying, [Phrases](../../transcription/phrase/index.md), [Parts](../../transcription/part/index.md) and [Scores](../../transcription/score/index.md). Each of these functions modifies the data passed to them. For example, the [Mod.repeat()](repeat.md) function creates repetitions of the given musical material:

```python
Mod.repeat(phrase, 41)
```

This will modify phrase to contain a total of 41 copies of the original musical material.

## Creating a Mod

Mod is a static utility; you don't instantiate it like other objects.  Call its methods on the class itself.  For example,

```python
Mod.fadeIn(score)
```

## Functions

The following Mod functions are always available:

### Volume

The following functions modify the volume (or dynamic) of notes in a phrase, part, or score:

| Function | Description |
|---|---|
| [`accent(material, meter)`](accent.md) | Make certain beats of each measure louder, in place. |
| [`compress(material, ratio)`](compress.md) | Squeeze or stretch the loudness range of the notes, in place. |
| [`crescendo(material, startTime, endTime, startVolume, endVolume)`](crescendo.md) | Slide the volume smoothly from one level to another over a span of time, in place. |
| [`fadeIn(material, fadeLength)`](fadeIn.md) | Fade the music up from silence to its normal volume, in place. |
| [`fadeOut(material, fadeLength)`](fadeOut.md) | Fade the music down from its normal volume to silence, in place. |
| [`normalize(material)`](normalize.md) | Scale every note's volume up so the loudest note reaches the maximum, in place. |

### Duration

The following functions modify the duration of notes in a phrase, part, or score.

| Function | Description |
|---|---|
| [`append(material1, material2)`](append.md) | Add the second material onto the end of the first, in place. |
| [`elongate(material, scaleFactor)`](elongate.md) | Stretch or squeeze every note's length by a scaling factor, in place. |
| [`changeLength(phrase, newLength)`](changeLength.md) | Stretch or squeeze a phrase so it lasts a set number of beats, in place. |
| [`cycle(phrase, numberOfNotes)`](cycle.md) | Repeat a phrase until it holds a set number of notes, in place. |
| [`palindrome(material)`](palindrome.md) | Double the music by adding a reversed copy of itself onto the end, in place. |
| [`repeat(material, times)`](repeat.md) | Repeat the music a set number of times, in place. |
| [`quantize(material, quantum)`](quantize.md) | Round note start times and durations to a grid, in place. |

**NOTE:** Use [cycle()](cycle.md) when you wish to fit a particular length. Use [repeat()](repeat.md) when you wish to repeat a particular number of times, regardless of length. When repeating overlapping phrases of different lengths, cycle() will guarantee they all end at approximately the same time.

### Pitch

The following functions modify the pitches of notes in a phrase, part, or score.

| Function | Description |
|---|---|
| [`invert(phrase, pitchAxis)`](invert.md) | Flip the pitches of a phrase around a center pitch, in place. |
| [`transpose(material, steps)`](transpose.md) | Shift the pitch of every note, in place. |
| [`retrograde(material)`](retrograde.md) | Reverse the order of the notes, in place. |
| [`rotate(phrase)`](rotate.md) | Shift the notes around the phrase, in place. |

### Panning

| [`bounce(material)`](bounce.md) | Pan notes hard left and right, alternating from note to note, in place. |


### Randomness

The following functions use randomness to modify notes in a phrase, part, or score.

| Function | Description |
|---|---|
| [`shuffle(material)`](shuffle.md) | Randomly reorder the notes, in place. |
| [`mutate(phrase)`](mutate.md) | Randomly change one note's pitch and one note's duration, in place. |
| [`randomize(material, pitchAmount)`](randomize.md) | Nudge each note's pitch, duration, and volume by random amounts, in place. |
| [`shake(material)`](shake.md) | Randomly vary the notes' volumes for an uneven, human feel, in place. |
| [`spread(material)`](spread.md) | Randomly pan the notes for an even spread across the stereo field, in place. |


### Other Functions

Here are some other mod functions:

| Function | Description |
|---|---|
| [`consolidate(part)`](consolidate.md) | Merge all of a part's phrases into a single phrase, in place. |
| [`fillRests(material)`](fillRests.md) | Replace each note-then-rest with one longer note, in place. |
| [`merge(material1, material2)`](merge.md) | Combine the second material into the first so they sound together, in place. |
| [`shift(material, time)`](shift.md) | Move every phrase's start time earlier or later, in place. |
| [`tiePitches(material)`](tiePitches.md) | Join neighboring notes of the same pitch into one longer note, in place. |
| [`tieRests(material)`](tieRests.md) | Join neighboring rests into one longer rest, in place. |
