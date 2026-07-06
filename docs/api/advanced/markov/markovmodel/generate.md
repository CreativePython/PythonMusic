# generate()

Generate a new sequence in the style the model learned.

Starts from startSequence and keeps adding symbols, each chosen at random by the model's odds, until it reaches the end of a sequence. If no start is given, the model picks one it has seen.

## Parameters

Once an object `markovmodel` has been created, you can use the following functions:

```python
markovmodel.generate()
```
```python
markovmodel.generate(startSequence)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `startSequence` | `list` | `None` | The symbols to start from. If omitted, the model picks a start it has learned. |

## Returns

`return chainList`

| Value | Type | Description |
|---|---|---|
| chainList | `list` | The generated sequence, starting with startSequence. |
