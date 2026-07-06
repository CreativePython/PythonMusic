# mapValueList()

Convert a list of numbers from one range to their matching places in another range.

Like [mapValue()](mapValue.md), but for a whole list, so each number must lie within the source range. A new list is returned; the original list is left unchanged.

## Parameters

```python
mapValueList(valueList, minValue, maxValue, minResult, maxResult)
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
