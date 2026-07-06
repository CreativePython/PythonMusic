# tiePitches()

Join neighboring notes of the same pitch into one longer note, in place.

Like a musical tie. This lowers the note count.

## Parameters

`Mod.tiePitches()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.tiePitches(material)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
