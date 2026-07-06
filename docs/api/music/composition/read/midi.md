# midi()

Read a MIDI file into a score, replacing the score's contents.

## Parameters

`Read.midi()` is a static utility. Call it on the `Read` class itself, for example:

```python
Read.midi(score, filename)
```
```python
Read.midi(score, filename, humanize)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `score` | `Score` | _required_ | The score to read the music into; its current contents are cleared. |
| `filename` | `str` | _required_ | The MIDI file to read (a .mid file). |
| `humanize` | `bool` | `False` | If True, give the notes their default sounding length (about 90% of their duration) for a more natural feel, instead of keeping the exact recorded timing. |

## Returns

`return score`

| Value | Type | Description |
|---|---|---|
| score | `Score` | The score, now holding the music from the file. |
