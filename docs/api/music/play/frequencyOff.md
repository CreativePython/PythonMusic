# frequencyOff()

Stop a frequency from sounding.

If the frequency is not sounding on this channel, nothing happens.

## Parameters

`Play.frequencyOff()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.frequencyOff(frequency)
```
```python
Play.frequencyOff(frequency, channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `frequency` | `float` | _required_ | The frequency to stop, in hertz (8.17 to 12600.0). |
| `channel` | `int` | `0` | The channel it is playing on, from 0 to 15. |
