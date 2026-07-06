# Write

You can create a MIDI file from your program using the [Write.midi()](midi.md) function. This function expects a [Score](../../transcription/score/index.md) ([Part](../../transcription/part/index.md), [Phrase](../../transcription/phrase/index.md), or [Note](../../transcription/note/index.md)) and a file name.

## Creating a Write

Write is a static utility; you don't instantiate it like other objects.  Call its methods on the class itself.  For example,

```python
Write.midi(score, "song.mid")
```

writes the musical data in score into the MIDI file called “song.mid”. This file is saved in the same folder as your program. If the MIDI file already exists, it will be overwritten.

## Functions

The following Write function is always available:

| Function | Description |
|---|---|
| [`midi(material, filename)`](midi.md) | Write music library material to a MIDI file. |
