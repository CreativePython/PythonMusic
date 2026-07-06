# midi()

Write music library material to a MIDI file.

If the file already exists, it is overwritten.

## Parameters

`Write.midi()` is a static utility. Call it on the `Write` class itself, for example:

```python
Write.midi(material, filename)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Note, Phrase, Part, or Score` | _required_ | The music to write. |
| `filename` | `str` | _required_ | The MIDI file to write (a .mid file). |
