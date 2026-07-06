# shake()

Randomly vary the notes' volumes for an uneven, human feel, in place.

## Parameters

`Mod.shake()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.shake(material)
```
```python
Mod.shake(material, amount)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
| `amount` | `int` | `20` | How strong the effect is. Each volume moves by up to this much, from 0 to 127. |
