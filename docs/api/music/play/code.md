# code()

Run your own functions in time with music library material.

Instead of making sound, each note triggers a function. The note's channel chooses
which function in actions to call, so actions needs one function per channel used.

## Parameters

`Play.code()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.code(material, actions)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Note, Phrase, Part, or Score` | _required_ | The music whose notes drive the timing. |
| `actions` | `list[function]` | _required_ | The functions to call, one per channel. |
