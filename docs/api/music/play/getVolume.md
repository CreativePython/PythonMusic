# getVolume()

Return the main volume for a channel.

## Parameters

`Play.getVolume()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.getVolume()
```
```python
Play.getVolume(channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `int` | `0` | The channel to read, from 0 to 15. |

## Returns

`return volume`

| Value | Type | Description |
|---|---|---|
| volume | `int` | The main volume, from 0 to 127. |
