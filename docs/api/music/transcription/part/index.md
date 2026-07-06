# Part

A Part object contains a set of [Phrase](../phrase/index.md) objects to be played by a particular instrument.  These phrase objects are played in parallel (i.e., simultaneously), and thus may overlap (according to their start times and durations).  Even if the particular instrument does not allow for polyphony (e.g., a flute), a part using this instrument can have different simultaneous melodies.  In other words, a part can be thought of as a group of several instruments of the same type (e.g., flutes), each playing a different melody (a phrase).

There are 128 different [instruments](../../constants/instrument.md) to pick from.

Parts may be assigned to one of sixteen MIDI channels (0 – 15) available on a standard computer’s audio system.  Each MIDI channel is capable of playing any of the 128 different instruments possible, but only one at a time. So, it is important to keep parts using different instruments in different MIDI channels. If two parts are using the same instrument, they may be assigned to the same MIDI channel.

MIDI channel 9 is reserved for percussion sounds.  Regardless of a part’s selected instrument, if that part is assigned to MIDI channel 9, its notes will generate [percussion sounds](../../constants/percussion.md), based on the notes’ pitches.

## Creating a Part

You can create a Part using the following functions:

```python
Part()
```

```python
Part(instrument)
```

```python
Part(instrument, channel)
```

```python
Part(title, instrument, channel)
```

```python
Part(phrase)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `instrument` | `int` | `None` | A [MIDI instrument](../../constants/instrument.md). |
| `channel` | `int` | `0` | A MIDI channel (0-15). |
| `title` | `str` | `''` | A title for the Part. |
| `phrase` | `Phrase` | `None` | The first Phrase to add to the Part. |

For example,

```python
part = Part("An example flute part", FLUTE, 0)
```

This creates a Part `part` with a descriptive title, using instrument `FLUTE` (see [instrument constants](../../constants/instrument.md) for a complete list of instruments), and assigned to MIDI channel 0 of the computer’s audio system.  Again, you should assign parts with different instruments to different MIDI channels (0-8, and 10-15).  Remember that MIDI channel 9 is dedicated to percussive sounds, as explained above.

## Functions

Once a Part `part` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`addPhrase(phrase)`](addPhrase.md) | Add a phrase to the part. |
| [`addPhraseList(phraseList)`](addPhraseList.md) | Add several phrases to the part at once. |

You can also set the instrument, tempo, dynamic, volume, panning, and title of the phrase.

| Function | Description |
|---|---|
| [`getInstrument()`](getInstrument.md) | Return the part's instrument. |
| [`setInstrument(instrument)`](setInstrument.md) | Set the part's instrument. |
| [`getTempo()`](getTempo.md) | Return the part's tempo. |
| [`setTempo(tempo)`](setTempo.md) | Set the part's tempo. |
| [`setDynamic(dynamic)`](setDynamic.md) | Set how loud every note in the part is. |
| [`getVolume()`](getVolume.md) | Return the part's volume. |
| [`setVolume(volume)`](setVolume.md) | Set the part's volume. |
| [`setPan(panning)`](setPan.md) | Set the stereo position of every note in the part. |
| [`getTitle()`](getTitle.md) | Return the part's title. |
| [`setTitle(title)`](setTitle.md) | Set the part's title. |

Finally, here are some additional Part functions:

| Function | Description |
|---|---|
| [`copy()`](copy.md) | Return a copy of the part. |
| [`empty()`](empty.md) | Remove every phrase from the part. |
| [`getSize()`](getSize.md) | Return how many phrases are in the part. |
| [`getPhraseList()`](getPhraseList.md) | Return the part's phrases. |
| [`getStartTime()`](getStartTime.md) | Return when the part starts. |
| [`getEndTime()`](getEndTime.md) | Return when the part ends. |
| [`getChannel()`](getChannel.md) | Return the part's MIDI channel. |
| [`setChannel(channel)`](setChannel.md) | Set the part's MIDI channel. |
