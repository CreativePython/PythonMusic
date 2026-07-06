# measureDataBySize()

Measure a list of size-and-count datasets.

Runs [bySize()](bySize.md) on each dataset and wraps the result as a measurement.

## Parameters

```python
measureDataBySize(datasets)
```
```python
measureDataBySize(datasets, metricName)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `datasets` | `list[list[list[int or float]]]` | _required_ | The datasets to measure. Each dataset is a [sizes, counts] pair of parallel lists. |
| `metricName` | `str` | `'BySize'` | A name to label the measurements with. |

## Returns

`return allMeasurements`

| Value | Type | Description |
|---|---|---|
| allMeasurements | `list[list]` | One row per dataset, each holding that dataset's measurement. |
