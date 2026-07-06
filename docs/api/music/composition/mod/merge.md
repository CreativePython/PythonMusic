# merge()

Combine the second material into the first so they sound together, in place.

Unlike [Mod.append()](append.md), which places the second material after the first, this overlaps them in time. Both materials must be the same kind (Part or Score). Make sure their instruments and channels fit together.

## Parameters

`Mod.merge()` is a static utility. Call it on the `Mod` class itself, for example:

```python
Mod.merge(material1, material2)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material1` | `Part or Score` | _required_ | The material to merge into; this one is changed. |
| `material2` | `Part or Score` | _required_ | The material to merge in; this one is left unchanged. |
