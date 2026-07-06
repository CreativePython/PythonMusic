# mapScale()

Map a number from one range to another, snapped to a musical scale.

Works like [mapValue()](mapValue.md), but rounds the result to the nearest pitch in the given
scale, so the output is always a usable MIDI pitch. A scale is a list of pitch
classes between 0 and 11 (see the scale constants such as MAJOR_SCALE). The key is
the scale's root pitch class, where 0 means C, 1 means C#/Db, … 11 means B; if it is
left out, the key is taken from minResultValue.

## Parameters

```python
mapScale(value, minValue, maxValue, minResult, maxResult)
```
```python
mapScale(value, minValue, maxValue, minResult, maxResult, scale, key)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `value` | `int or float` | _required_ | The number to convert; it must be between minValue and maxValue. |
| `minValue` | `int or float` | _required_ | The low end of the source range (inclusive). |
| `maxValue` | `int or float` | _required_ | The high end of the source range (inclusive). |
| `minResult` | `int or float` | _required_ | The low end of the destination range (inclusive). |
| `maxResult` | `int or float` | _required_ | The high end of the destination range (inclusive). |
| `scale` | `list[int]` | `None` | The scale to snap to, a list of pitch classes between 0 and 11. If omitted, every pitch is allowed (the chromatic scale). |
| `key` | `int` | `None` | The scale's root pitch class, from 0 to 11. If omitted, it is taken from `minResult`. |

## Returns

`return mappedValue`

| Value | Type | Description |
|---|---|---|
| mappedValue | `int or float` | The mapped number, snapped to the scale as a MIDI pitch. |
