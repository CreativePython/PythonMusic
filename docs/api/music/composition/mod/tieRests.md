# tieRests()

Join neighboring rests into one longer rest, in place.

This lowers the note count.

## Parameters

`Mod.tieRests()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.tieRests(material)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
