# setPan()

Set the stereo position of every note in the part.

## Parameters

Once an object `part` has been created, you can use the following function:

```python
part.setPan(panning)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `panning` | `int or float` | _required_ | The stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right). |
