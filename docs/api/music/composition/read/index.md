# Read

You can read a MIDI file into your program using the [Read.midi()](midi.md) function. This function expects an empty score and the name of a MIDI file (saved in the same folder as your program).

## Creating a Read

Read is a static utility; you don't instantiate it like other objects.  Call its methods on the class itself.  For example,

```python
Read.midi(score, "song.mid")
```

inputs the musical data from the MIDI file “song.mid”, and stores them into `score`. Once the file has been read in, then you can manipulate or playback the score. For example,

```python
from music import *

score = Score()               # create an empty score
Read.midi(score, "song.mid")  # read MIDI file into it

Play.midi(score)              # play it back
```

A Score created from an external MIDI file may not be as nicely structured (in terms of Parts, Phrases, and Notes) as a Score created manually through your program. However, you can still use Score.getPartList(), Part.getPhraseList(), and Phrase.getNoteList() to extract its musical material, and use it as you see fit.

## Functions

The following Read function is always available:

| Function | Description |
|---|---|
| [`midi(score, filename)`](midi.md) | Read a MIDI file into a score, replacing the score's contents. |
