# setTimeSignature()

Set the score's time signature.

For example, setTimeSignature(3, 4) sets 3/4 time.

## Parameters

Once an object `score` has been created, you can use the following function:

```python
score.setTimeSignature(numerator, denominator)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `numerator` | `int` | _required_ | The number of beats per measure (the top number). |
| `denominator` | `int` | _required_ | The note value that counts as one beat (the bottom number). |
