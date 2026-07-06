# rotate()

Shift the notes around the phrase, in place.

Each shift moves the last note to the front, so the first note becomes the second, and so on.

## Parameters

`Mod.rotate()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.rotate(phrase)
```
```python
Mod.rotate(phrase, times)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `phrase` | `Phrase` | _required_ | The phrase to change. |
| `times` | `int` | `1` | How many notes to shift by. |
