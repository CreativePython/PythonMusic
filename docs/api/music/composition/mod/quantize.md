# quantize()

Round note start times and durations to a grid, in place.

Each note's start time and duration are rounded to the nearest multiple of quantum. A smaller quantum changes the music less; a larger one makes it sound more mechanical. If a scale is given, pitches are also snapped to it.

## Parameters

`Mod.quantize()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.quantize(material, quantum)
```
```python
Mod.quantize(material, quantum, scale, key)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Note, Phrase, Part, or Score` | _required_ | The music to change. |
| `quantum` | `int or float` | _required_ | The grid size to round to, in beats. |
| `scale` | `list[int]` | `CHROMATIC_SCALE` | A scale to snap pitches to, a list of pitch classes between 0 and 11. If omitted, pitches are left alone. |
| `key` | `int` | `0` | The scale's root pitch class, from 0 to 11, where 0 means C. |
