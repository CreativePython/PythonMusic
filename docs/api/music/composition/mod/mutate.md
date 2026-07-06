# mutate()

Randomly change one note's pitch and one note's duration, in place.

The new pitch is picked between the phrase's lowest and highest notes; the new duration is picked from those already in the phrase.

## Parameters

`Mod.mutate()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.mutate(phrase)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `phrase` | `Phrase` | _required_ | The phrase to change. |
