# get()

Pick a random symbol to follow a context, weighted by how often each was seen.

The context must already exist in the model.

## Parameters

Once an object `markovmodel` has been created, you can use the following function:

```python
markovmodel.get(tupleOfSymbols)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tupleOfSymbols` | `tuple` | _required_ | The context to follow on from. |

## Returns

`return symbol`

| Value | Type | Description |
|---|---|---|
| symbol | `object` | A symbol chosen at random from those that have followed the context, weighted by how often each was seen. |
