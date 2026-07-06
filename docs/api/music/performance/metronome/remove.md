# remove()

Remove a scheduled function from the metronome.

If the function was scheduled several times, the earliest one is removed; call again to remove more.

## Parameters

Once an object `metronome` has been created, you can use the following function:

```python
metronome.remove(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to remove. |
