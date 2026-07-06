# add()

Schedule a function for the metronome to call on a given beat.

## Parameters

Once an object `metronome` has been created, you can use the following functions:

```python
metronome.add(action)
```
```python
metronome.add(action, parameters, desiredBeat, repeatFlag)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call. |
| `parameters` | `list` | `[]` | The parameters to pass to the function. |
| `desiredBeat` | `int` | `0` | Which beat to call it on. 0 means the very next beat, 1 the first beat of the measure, 2 the second, and so on. A beat past the end of the measure carries into later measures. |
| `repeatFlag` | `bool` | `False` | Whether to call it every time that beat comes around (True) or just once (False). |
