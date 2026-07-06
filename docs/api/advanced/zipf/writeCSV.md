# writeCSV()

Write measurements to a CSV file.

Takes the measurements returned by [measureScore()](measureScore.md) or [measureMidi()](measureMidi.md) and writes them to a spreadsheet file, one row per score.

## Parameters

```python
writeCSV(measurements, filename)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `measurements` | `list[list]` | _required_ | The measurements to write, as returned by [measureScore()](measureScore.md) or [measureMidi()](measureMidi.md). |
| `filename` | `str` | _required_ | The CSV file to write. |
