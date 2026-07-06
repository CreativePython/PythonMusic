# learn()

Learn the patterns in a sequence of symbols, at every order.

Trains each of the model's orders on the sequence. Call it more than once to keep training on further sequences.

## Parameters

Once an object `compositemarkovmodel` has been created, you can use the following function:

```python
compositemarkovmodel.learn(listOfSymbols)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `listOfSymbols` | `list` | _required_ | The sequence to learn from. |
