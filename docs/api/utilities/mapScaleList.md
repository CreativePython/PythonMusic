# mapScaleList()

Convert a list of numbers from one range to their matching places in another range.

Like [mapScale()](mapScale.md), but for a whole list. A new list is returned; the original list is left unchanged.

## Parameters

```python
mapScaleList(valueList, minValue, maxValue, minResult, maxResult)
```
```python
mapScaleList(valueList, minValue, maxValue, minResult, maxResult, scale, key)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `valueList` | `list[int or float]` | _required_ | The numbers to convert. |
| `minValue` | `int or float` | _required_ | The low end of the source range (inclusive). |
| `maxValue` | `int or float` | _required_ | The high end of the source range (inclusive). |
| `minResult` | `int or float` | _required_ | The low end of the destination range (inclusive). |
| `maxResult` | `int or float` | _required_ | The high end of the destination range (inclusive). |
| `scale` | `list[int]` | `None` | The scale to snap to, a list of pitch classes between 0 and 11. If omitted, every pitch is allowed (the chromatic scale). |
| `key` | `int` | `None` | The scale's root pitch class, from 0 to 11. If omitted, it is taken from `minResult`. |

## Returns

`return mappedList`

| Value | Type | Description |
|---|---|---|
| mappedList | `list[int or float]` | Each number's matching place in the destination range, snapped to the scale as a MIDI pitch. |
