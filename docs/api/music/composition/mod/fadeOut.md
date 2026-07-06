# fadeOut()

Fade the music down from its normal volume to silence, in place.

## Parameters

`Mod.fadeOut()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.fadeOut(material, fadeLength)
```
```python
Mod.fadeOut(material, fadeLength, _endTime)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
| `fadeLength` | `int or float` | _required_ | How long the fade lasts, in beats. |
| `_endTime` | `int or float` | `None` | Internal use; leave unset. |
