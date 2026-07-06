# play()

Play music library material through the output device.

Works like Play.midi().

## Parameters

Once an object `midiout` has been created, you can use the following function:

```python
midiout.play(material)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Note, Phrase, Part, or Score` | _required_ | The music to play. |
