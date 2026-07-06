# mapValue()

Convert a number from one range to its matching place in another range.

For example, 5 in the range 0 to 10 maps to 50 in the range 0 to 100. The number must lie within the source range; to allow numbers outside it, use [map()](map.md) instead.

## Parameters

```python
mapValue(value, minValue, maxValue, minResult, maxResult)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `value` | `int or float` | _required_ | The number to convert; it must be between minValue and maxValue. |
| `minValue` | `int or float` | _required_ | The low end of the source range (inclusive). |
| `maxValue` | `int or float` | _required_ | The high end of the source range (inclusive). |
| `minResult` | `int or float` | _required_ | The low end of the destination range (inclusive). |
| `maxResult` | `int or float` | _required_ | The high end of the destination range (inclusive). |

## Returns

`return mappedValue`

| Value | Type | Description |
|---|---|---|
| mappedValue | `int or float` | The number's matching place in the destination range. It is an int if minResult is an int, otherwise a float. |
