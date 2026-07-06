# randomize()

Nudge each note's pitch, duration, and volume by random amounts, in place.

Each value changes by a random amount within plus or minus the amount you give. Set an amount to 0 to leave that property alone.

## Parameters

`Mod.randomize()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.randomize(material, pitchAmount)
```
```python
Mod.randomize(material, pitchAmount, durationAmount, volumeAmount)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Note, Phrase, Part, or Score` | _required_ | The music to change. |
| `pitchAmount` | `int` | _required_ | The most each pitch may move, in semitones (keep results within 0 to 127). |
| `durationAmount` | `int or float` | `0` | The most each duration may move, in beats. |
| `volumeAmount` | `int` | `0` | The most each volume may move, from 0 to 127. |
