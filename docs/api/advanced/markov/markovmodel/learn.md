# learn()

Learn the patterns in a sequence of symbols.

Pulls the n-grams out of the list and adds their transitions to the model. Call it more than once to keep training the model on further sequences.

## Parameters

Once an object `markovmodel` has been created, you can use the following function:

```python
markovmodel.learn(listOfSymbols)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `listOfSymbols` | `list` | _required_ | The sequence to learn from. |
