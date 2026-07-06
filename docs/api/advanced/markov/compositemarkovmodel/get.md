# get()

Pick a random symbol to follow a context, using the longest order that fits.

Tries the highest order first and falls back to shorter contexts as needed.

## Parameters

Once an object `compositemarkovmodel` has been created, you can use the following function:

```python
compositemarkovmodel.get(tupleOfSymbols)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tupleOfSymbols` | `tuple` | _required_ | The context to follow on from. |

## Returns

`return nextSymbol`

| Value | Type | Description |
|---|---|---|
| nextSymbol | `object` | A symbol chosen at random from those that have followed the context, using the longest order that fits. |
