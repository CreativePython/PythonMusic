# fadeIn()

Fade the music up from silence to its normal volume, in place.

## Parameters

`Mod.fadeIn()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.fadeIn(material, fadeLength)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
| `fadeLength` | `int or float` | _required_ | How long the fade lasts, in beats. |
