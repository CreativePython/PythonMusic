# measureMidi()

Measure a list of MIDI files against a list of Zipf metrics.

Reads each MIDI file into a score, then measures the scores like [measureScore()](measureScore.md).

## Parameters

```python
measureMidi(files, metrics)
```
```python
measureMidi(files, metrics, quantum)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `files` | `list[str]` | _required_ | The paths of the MIDI files to measure. |
| `metrics` | `list[Metric]` | _required_ | The Zipf metrics to apply. |
| `quantum` | `float` | `0.25` | The rhythmic grid to measure on, in beats, where 0.25 is a sixteenth note. |

## Returns

`return allMeasurements`

| Value | Type | Description |
|---|---|---|
| allMeasurements | `list[list]` | One row per file. Each row holds the file's measurement for each metric, followed by the score's title. |
