# setAttackTimesAndVolumes()

Set the envelope's attack times and the volumes reached at them.

The two lists are parallel and must be the same length.

## Parameters

Once an object `envelope` has been created, you can use the following function:

```python
envelope.setAttackTimesAndVolumes(attackTimes, attackVolumes)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `attackTimes` | `list[int]` | _required_ | The attack times, in milliseconds, each measured from the previous one (the first from the start of the sound). |
| `attackVolumes` | `list[float]` | _required_ | The volumes to reach at those times, each from 0.0 to 1.0. |
