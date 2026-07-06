# shuffle()

Randomly reorder the notes, in place.

Every note is kept; only their order changes.

## Parameters

`Mod.shuffle()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.shuffle(material)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
