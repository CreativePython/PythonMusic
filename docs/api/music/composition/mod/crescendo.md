# crescendo()

Slide the volume smoothly from one level to another over a span of time, in place.

Use a rising volume for a crescendo or a falling one for a diminuendo.

## Parameters

`Mod.crescendo()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.crescendo(material, startTime, endTime, startVolume, endVolume)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Phrase, Part, or Score` | _required_ | The music to change. |
| `startTime` | `int or float` | _required_ | When the slide begins, in beats. |
| `endTime` | `int or float` | _required_ | When the slide ends, in beats. |
| `startVolume` | `int or float` | _required_ | The volume at the start, from 0 to 127. |
| `endVolume` | `int or float` | _required_ | The volume at the end, from 0 to 127. |
