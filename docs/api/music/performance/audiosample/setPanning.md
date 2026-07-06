# setPanning()

Set the sample's stereo position.

## Parameters

Once an object `audiosample` has been created, you can use the following functions:

```python
audiosample.setPanning(panning)
```
```python
audiosample.setPanning(panning, voice)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `panning` | `int` | _required_ | Stereo position from 0 (left) to 127 (right). |
| `voice` | `int` | `0` | Which voice to set, from 0 to one less than the number of voices. |
