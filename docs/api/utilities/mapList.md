# mapList()

Convert a list of numbers from one range to their matching places relative to another range.

Like [map()](map.md), but for a whole list, so numbers may lie outside the source range. A new list is returned; the original list is left unchanged.

## Parameters

```python
mapList(valueList, minValue, maxValue, minResult, maxResult)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `valueList` | `list[int or float]` | _required_ | The numbers to convert. |
| `minValue` | `int or float` | _required_ | The low end of the source range (inclusive). |
| `maxValue` | `int or float` | _required_ | The high end of the source range (inclusive). |
| `minResult` | `int or float` | _required_ | The low end of the destination range (inclusive). |
| `maxResult` | `int or float` | _required_ | The high end of the destination range (inclusive). |

## Returns

`return mappedList`

| Value | Type | Description |
|---|---|---|
| mappedList | `list[int or float]` | Each number's matching place in the destination range. |
