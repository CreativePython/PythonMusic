# MarkovModel

A Markov model records which symbols tend to follow which, then uses those odds to produce fresh sequences. The order sets how much history each step looks back on. A first-order model (order 1) looks at one symbol to pick the next (bigram probabilities). A second-order model (order 2) looks at the previous pair (trigram probabilities), and so on.

Train the model with [learn()](learn.md), then make new sequences with [generate()](generate.md). A symbol can be anything. For music it is usually a pitch.

## Creating a MarkovModel

You can create a MarkovModel using the following functions:

```python
MarkovModel()
```

```python
MarkovModel(order)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `order` | `int` | `1` | How many previous symbols each step looks back on. |

For example,

```python
model = MarkovModel(3)
```

## Functions

Once a MarkovModel `model` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`clear()`](clear.md) | Empty the model, forgetting everything it has learned. |
| [`learn(listOfSymbols)`](learn.md) | Learn the patterns in a sequence of symbols. |
| [`put(tupleOfSymbols)`](put.md) | Add a single transition to the model by hand. |
| [`get(tupleOfSymbols)`](get.md) | Pick a random symbol to follow a context, weighted by how often each was seen. |
| [`getTransitions(tupleOfSymbols)`](getTransitions.md) | Return every symbol that has followed a context, with how often each did. |
| [`generate()`](generate.md) | Generate a new sequence in the style the model learned. |
| [`getNumberOfSymbols()`](getNumberOfSymbols.md) | Return how many different symbols the model has learned. |
| [`getNumberOfTransitions()`](getNumberOfTransitions.md) | Return how many transitions the model has learned. |
