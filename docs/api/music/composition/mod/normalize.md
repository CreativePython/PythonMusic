# normalize()

Scale every note's volume up so the loudest note reaches the maximum, in place.

The notes keep their relative loudness.

## Parameters

`Mod.normalize()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.normalize(material)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
