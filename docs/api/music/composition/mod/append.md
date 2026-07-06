# append()

Add the second material onto the end of the first, in place.

Both materials must be the same kind. For two notes, the first note's duration is extended (its pitch is unchanged).

## Parameters

`Mod.append()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.append(material1, material2)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material1` | `Note, Phrase, Part, or Score` | _required_ | The material to add onto; this one is changed. |
| `material2` | `Note, Phrase, Part, or Score` | _required_ | The material to append. |
