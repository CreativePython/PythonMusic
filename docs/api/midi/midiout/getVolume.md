# getVolume()

Return the main volume for a channel.

## Parameters

Once an object `midiout` has been created, you can use the following functions:

```python
midiout.getVolume()
```
```python
midiout.getVolume(channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `int` | `0` | The channel to read, from 0 to 15. |

## Returns

`return volume`

| Value | Type | Description |
|---|---|---|
| volume | `int` | The main volume, from 0 to 127. |
