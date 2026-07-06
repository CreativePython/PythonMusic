# changeLength()

Stretch or squeeze a phrase so it lasts a set number of beats, in place.

Like [Mod.elongate()](elongate.md), but you give the final length rather than a scaling factor.

## Parameters

`Mod.changeLength()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.changeLength(phrase, newLength)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `phrase` | `Phrase` | _required_ | The phrase to change. |
| `newLength` | `int or float` | _required_ | The phrase's new total length, in beats. |
