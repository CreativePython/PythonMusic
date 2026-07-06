# setDuration()

Set how long the note lasts in the written score.

The note's length is adjusted to keep the same proportion to the duration.

## Parameters

Once an object `note` has been created, you can use the following function:

```python
note.setDuration(duration)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `duration` | `int or float` | _required_ | The new duration, as a float where 1.0 is a quarter note. |
