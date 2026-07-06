# setTimeSignature()

Set the metronome's time signature.

## Parameters

Once an object `metronome` has been created, you can use the following function:

```python
metronome.setTimeSignature(timeSignature)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `timeSignature` | `list[int]` | _required_ | The time signature as [beats, beatValue], for example [4, 4] for 4/4. |
