# repeat()

Repeat the music a set number of times, in place.

For example, Mod.repeat(phrase, 2) makes the phrase play twice.

## Parameters

`Mod.repeat()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.repeat(material, times)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
| `times` | `int` | _required_ | How many times the music should appear. |
