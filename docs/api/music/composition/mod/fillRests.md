# fillRests()

Replace each note-then-rest with one longer note, in place.

Lengthens a note to absorb the rest that follows it and removes the rest, lowering the note count.

## Parameters

`Mod.fillRests()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.fillRests(material)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
