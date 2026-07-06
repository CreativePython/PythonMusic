# bySize()

Measure the Zipf slope of a set of counts plotted against given sizes.

Like [byRank()](byRank.md), but plots the counts against the sizes you supply rather than against automatic ranks, on a log-log scale, then fits a trendline.

## Parameters

```python
bySize(sizes, counts)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sizes` | `Iterable[int or float]` | _required_ | The size (the x value) for each count. |
| `counts` | `Iterable[int or float]` | _required_ | How often each item occurs. |

## Returns

`return slope, r2, yint`

| Value | Type | Description |
|---|---|---|
| slope | `float` | The slope of the fitted trendline. |
| r2 | `float` | How well the trendline fits the data, from 0.0 to 1.0. |
| yint | `float` | The trendline's y-intercept. |
