# getAttackTimesAndVolumes()

Return the envelope's attack times and the volumes reached at them.

## Parameters

Once an object `envelope` has been created, you can use the following function:

```python
envelope.getAttackTimesAndVolumes()
```

## Returns

`return attackTimes, attackVolumes`

| Value | Type | Description |
|---|---|---|
| attackTimes | `list[int]` | The attack times, in milliseconds. |
| attackVolumes | `list[float]` | The volumes reached at those times, each from 0.0 to 1.0. |
