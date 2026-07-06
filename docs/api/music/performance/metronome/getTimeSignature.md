# getTimeSignature()

Return the metronome's time signature.

## Parameters

Once an object `metronome` has been created, you can use the following function:

```python
metronome.getTimeSignature()
```

## Returns

`return timeSignature`

| Value | Type | Description |
|---|---|---|
| timeSignature | `list[int]` | The time signature as [beats, beatValue], for example [4, 4] for 4/4. |
