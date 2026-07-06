# notate()

Show the music as staff notation.

Notation handles only a single phrase at a time (use [Mod.consolidate()](../mod/consolidate.md) to combine a part's phrases first). It also lets you enter music as notation and save it.

## Parameters

`View.notate()` is a static utility. Call it on the `View` class itself, for example:

```python
View.notate(material)
```
```python
View.notate(material, writeToFile)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Note, Phrase, Part, or Score` | _required_ | The music to show. |
| `writeToFile` | `bool` | `False` | Whether to also save the notation to a file. |
