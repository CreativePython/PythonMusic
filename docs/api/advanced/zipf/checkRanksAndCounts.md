# checkRanksAndCounts()

Check that ranks and counts are valid for a Zipf measurement.

Confirms that both lists hold at least one item, are the same length, and contain no zero or negative values. On bad input, prints an error rather than raising.

## Parameters

```python
checkRanksAndCounts(ranks, counts)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ranks` | `list[int or float]` | _required_ | The rank (the x value) for each count. |
| `counts` | `list[int or float]` | _required_ | How often each item occurs. |
