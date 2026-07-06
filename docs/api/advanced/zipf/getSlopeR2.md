# getSlopeR2()

Fit a Zipf trendline to a set of ranks and counts.

Fits a trendline to the rank-against-count plot on a log-log scale and returns its slope, fit, and y-intercept. If the slope or fit cannot be worked out, zero is returned for it. Two special cases: a single repeated value (a vertical trendline) gives a slope and fit of 0; a perfectly even spread (a horizontal trendline) gives a slope of 0 and a fit of 1.

## Parameters

```python
getSlopeR2(ranks, counts)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ranks` | `list[int or float]` | _required_ | The rank (the x value) for each count. |
| `counts` | `list[int or float]` | _required_ | How often each item occurs. |

## Returns

`return slope, r2, yint`

| Value | Type | Description |
|---|---|---|
| slope | `float` | The slope of the fitted trendline. |
| r2 | `float` | How well the trendline fits the data, from 0.0 to 1.0. |
| yint | `float` | The trendline's y-intercept. |
