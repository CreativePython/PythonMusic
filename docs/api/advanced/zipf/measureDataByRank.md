# measureDataByRank()

Measure a list of count datasets by rank.

Runs [byRank()](byRank.md) on each dataset and wraps the result as a measurement.

## Parameters

```python
measureDataByRank(datasets)
```
```python
measureDataByRank(datasets, metricName)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `datasets` | `list[list[int or float]]` | _required_ | The datasets to measure. Each dataset is a list of counts. |
| `metricName` | `str` | `'ByRank'` | A name to label the measurements with. |

## Returns

`return allMeasurements`

| Value | Type | Description |
|---|---|---|
| allMeasurements | `list[list]` | One row per dataset, each holding that dataset's measurement. |
