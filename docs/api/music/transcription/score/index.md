# Score

A Score object contains a set of [Part](../part/index.md) objects.  Score contents (parts, phrases, notes) are algorithmically generated, or read from a standard MIDI file (see [Read](../../composition/read/index.md)).  Scores can be written to standard MIDI files (see [Write](../../composition/write/index.md)).

## Creating a Score

You can create a Score using the following functions:

```python
Score()
```

```python
Score(title)
```

```python
Score(tempo)
```

```python
Score(title, tempo)
```

```python
Score(part)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `title` | `str` | `''` | A title for the Score. |
| `tempo` | `int or float` | `60.0` | 
| `part` | `Part` | `None` | The first Part to add to the Score. |

For example,

```python
score = Score("Morning Glory", 135.0)
```

This creates a Score `score` with the descriptive title “Morning Glory”, with a tempo of 135 beats per minute.

## Functions

Once a Score `score` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`addPart(part)`](addPart.md) | Add a part to the score. |
| [`addPartList(partList)`](addPartList.md) | Add several parts to the score at once. |

You can also set the tempo, volume, panning, and title of the score.

| Function | Description |
|---|---|
| [`getTempo()`](getTempo.md) | Return the score's tempo. |
| [`setTempo(tempo)`](setTempo.md) | Set the score's tempo. |
| [`getVolume()`](getVolume.md) | Return the score's volume. |
| [`setVolume(volume)`](setVolume.md) | Set the score's volume. |
| [`setPan(pan)`](setPan.md) | Set the stereo position of every note in the score. |
| [`getTitle()`](getTitle.md) | Return the score's title. |
| [`setTitle(title)`](setTitle.md) | Set the score's title. |

Finally, here are some additional Score functions:

| Function | Description |
|---|---|
| [`copy()`](copy.md) | Return a copy of the score. |
| [`empty()`](empty.md) | Remove every part from the score. |
| [`getSize()`](getSize.md) | Return how many parts are in the score. |
| [`getPartList()`](getPartList.md) | Return the score's parts. |
| [`getStartTime()`](getStartTime.md) | Return when the score starts. |
| [`getEndTime()`](getEndTime.md) | Return when the score ends. |
| [`setTimeSignature(numerator, denominator)`](setTimeSignature.md) | Set the score's time signature. |
| [`getNumerator()`](getNumerator.md) | Return the top number of the score's time signature. |
| [`getDenominator()`](getDenominator.md) | Return the bottom number of the score's time signature. |
| [`getKeyQuality()`](getKeyQuality.md) | Return the score's key quality (major or minor). |
| [`setKeyQuality(quality)`](setKeyQuality.md) | Set the score's key quality (major or minor). |
| [`getKeySignature()`](getKeySignature.md) | Return the score's key signature. |
| [`setKeySignature(signature)`](setKeySignature.md) | Set the score's key signature. |
