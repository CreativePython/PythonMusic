# compress()

Squeeze or stretch the loudness range of the notes, in place.

Each note's loudness is moved toward or away from the average by the given ratio: 0 makes every note the average loudness, 1 leaves it unchanged, and 2 makes every note twice as far from the average. Negative values flip notes to the other side of the average.

## Parameters

`Mod.compress()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.compress(material, ratio)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Note, Phrase, Part, or Score` | _required_ | The music to change. |
| `ratio` | `int or float` | _required_ | How much to squeeze (below 1) or stretch (above 1) the loudness range. |
