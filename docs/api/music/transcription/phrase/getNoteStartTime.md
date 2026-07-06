# getNoteStartTime()

Return when the note at a given position starts.

## Parameters

Once an object `phrase` has been created, you can use the following function:

```python
phrase.getNoteStartTime(index)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `index` | `int` | _required_ | The note's position, where 0 is the first note. |

## Returns

`return startTime`

| Value | Type | Description |
|---|---|---|
| startTime | `int or float` | The note's start time, in beats from the start of the phrase. |
