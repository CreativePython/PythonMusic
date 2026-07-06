# getTransitions()

Return every symbol that has followed a context, with how often each did.

The context must already exist in the model. The two lists are parallel.

## Parameters

Once an object `markovmodel` has been created, you can use the following function:

```python
markovmodel.getTransitions(tupleOfSymbols)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tupleOfSymbols` | `tuple` | _required_ | The context to look up. |

## Returns

`return symbolList, countList, total`

| Value | Type | Description |
|---|---|---|
| symbolList | `list` | The symbols that have followed the context. |
| countList | `list[int]` | How many times each symbol followed it. |
| total | `int` | The total of all the counts. |
