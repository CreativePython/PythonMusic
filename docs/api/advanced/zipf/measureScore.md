# measureScore()

Measure a list of scores against a list of Zipf metrics.

Runs every metric on every score and collects the results.

## Parameters

```python
measureScore(scores, metrics)
```
```python
measureScore(scores, metrics, quantum)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `scores` | `list[Score]` | _required_ | The scores to measure. |
| `metrics` | `list[Metric]` | _required_ | The Zipf metrics to apply. |
| `quantum` | `float` | `0.25` | The rhythmic grid to measure on, in beats, where 0.25 is a sixteenth note. |

## Returns

`return allMeasurements`

| Value | Type | Description |
|---|---|---|
| allMeasurements | `list[list]` | One row per score. Each row holds the score's measurement for each metric, followed by the score's title. |
