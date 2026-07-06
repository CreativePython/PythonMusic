# map()

Convert a number from one range to another, including values outside the source range.

For example, 5 in the range 0 to 10 maps to 50 in the range 0 to 100. The number may lie outside the source range: it is then carried just as far outside the destination range (for example, 15 in the range 0 to 10 maps to 150 in the range 0 to 100). To require the number to stay within the source range instead, use [mapValue()](mapValue.md).

## Parameters

```python
map(value, minValue, maxValue, minResult, maxResult)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `value` | `int or float` | _required_ | The number to convert. |
| `minValue` | `int or float` | _required_ | The low end of the source range (inclusive). |
| `maxValue` | `int or float` | _required_ | The high end of the source range (inclusive). |
| `minResult` | `int or float` | _required_ | The low end of the destination range (inclusive). |
| `maxResult` | `int or float` | _required_ | The high end of the destination range (inclusive). |

## Returns

`return mappedValue`

| Value | Type | Description |
|---|---|---|
| mappedValue | `int or float` | The number's matching place relative to the destination range. It is an int if minResult is an int, otherwise a float. |
