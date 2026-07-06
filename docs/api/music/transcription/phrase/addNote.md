# addNote()

Add a note to the end of the phrase.

Give a ready-made Note, or give a pitch and a duration and one is built for you.

## Parameters

Once an object `phrase` has been created, you can use the following functions:

```python
phrase.addNote(note)
```
```python
phrase.addNote(note, duration)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `note` | `Note or int or float` | _required_ | A Note to add, or a MIDI pitch (or frequency) to build one from. |
| `duration` | `int or float` | `None` | The note's duration (a float where 1.0 is a quarter note), used when building a note from a pitch. |
