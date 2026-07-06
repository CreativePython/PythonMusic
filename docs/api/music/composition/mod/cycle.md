# cycle()

Repeat a phrase until it holds a set number of notes, in place.

Like [Mod.repeat()](repeat.md), but the last repetition may be cut short once the note count is reached.

## Parameters

`Mod.cycle()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.cycle(phrase, numberOfNotes)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `phrase` | `Phrase` | _required_ | The phrase to change. |
| `numberOfNotes` | `int` | _required_ | How many notes the phrase should end up with. |
