# getPanning()

Return the main stereo position for a channel.

## Parameters

`Play.getPanning()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.getPanning()
```
```python
Play.getPanning(channel)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `channel` | `int` | `0` | The channel to read, from 0 to 15. |

## Returns

`return panning`

| Value | Type | Description |
|---|---|---|
| panning | `int` | Stereo position from 0 (left) through 64 (center) to 127 (right). |
