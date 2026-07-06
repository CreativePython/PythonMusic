# generate()

Generate a new sequence in the style the model learned.

Starts from startSequence and keeps adding symbols until it reaches the end of a sequence. The context grows up to maxOrder as it goes. If no start is given, the model picks one it has seen.

## Parameters

Once an object `compositemarkovmodel` has been created, you can use the following functions:

```python
compositemarkovmodel.generate()
```
```python
compositemarkovmodel.generate(startSequence)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `startSequence` | `list` | `None` | The symbols to start from. If omitted, the model picks a start it has learned. |

## Returns

`return chainList`

| Value | Type | Description |
|---|---|---|
| chainList | `list` | The generated sequence, starting with startSequence. |
