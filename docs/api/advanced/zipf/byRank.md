# byRank()

Measure the Zipf slope of a set of counts, ranked from largest to smallest.

Ranks the counts from largest to smallest, then fits a trendline to the rank-against- count plot on a log-log scale. A slope close to -1 with a good fit indicates a Zipf-like distribution.

## Parameters

```python
byRank(counts)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `counts` | `Iterable[int or float]` | _required_ | How often each item occurs. |

## Returns

`return slope, r2, yint`

| Value | Type | Description |
|---|---|---|
| slope | `float` | The slope of the fitted trendline. |
| r2 | `float` | How well the trendline fits the data, from 0.0 to 1.0. |
| yint | `float` | The trendline's y-intercept. |
