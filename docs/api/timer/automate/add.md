# add()

Register a function to be called once every frame.

Use [setRate()](setRate.md) to change how often that is.

## Parameters

`Automate.add()` is a static utility. Call it on the `Automate` class itself, for example:

```python
Automate.add(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call; it receives no parameters. |
