# consolidate()

Merge all of a part's phrases into a single phrase, in place.

Handy before [View.notate()](../view/notate.md), which shows only one phrase at a time.

## Parameters

`Mod.consolidate()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.consolidate(part)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `part` | `Part` | _required_ | The part to change. |
