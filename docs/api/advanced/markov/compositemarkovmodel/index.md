# CompositeMarkovModel

A CompositeMarkovModel holds one model for each order from 1 up to maxOrder. When choosing the next symbol, it tries the highest order first and falls back to a shorter context when the longer one has not been seen. This keeps the style of a high-order model while still being able to continue from contexts it has not met before.

Train it with [learn()](learn.md), then make new sequences with [generate()](generate.md).

## Creating a CompositeMarkovModel

You can create a CompositeMarkovModel using the following function:

```python
CompositeMarkovModel(maxOrder)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `maxOrder` | `int` | _required_ | The highest order to use. The model holds every order from 1 up to this. |

For example,

```python
model = CompositeMarkovModel(4)
```

## Functions

Once a CompositeMarkovModel `model` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`learn(listOfSymbols)`](learn.md) | Learn the patterns in a sequence of symbols, at every order. |
| [`get(tupleOfSymbols)`](get.md) | Pick a random symbol to follow a context, using the longest order that fits. |
| [`generate()`](generate.md) | Generate a new sequence in the style the model learned. |
| [`isConnected(context)`](isConnected.md) | Report whether the model can continue from a context. |
