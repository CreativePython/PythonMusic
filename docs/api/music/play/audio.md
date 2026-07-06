# audio()

Play music library material using audio samples as the instruments.

Each channel in the material is played by the audio sample at the same position in
audioSamples. The optional loopFlags and envelopes lists are parallel to
audioSamples.

## Parameters

`Play.audio()` is a static utility. Call it on the `Play` class itself, for example:

```python
Play.audio(material, audioSamples)
```
```python
Play.audio(material, audioSamples, loopFlags, envelopes)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `material` | `Note, Phrase, Part, or Score` | _required_ | The music to play. |
| `audioSamples` | `list[AudioSample]` | _required_ | The audio samples to play with, one per channel. |
| `loopFlags` | `list[bool]` | `[]` | Whether to loop each sample if a note outlasts it. Defaults to no looping. |
| `envelopes` | `list[Envelope]` | `[]` | An envelope to shape each sample's volume over time. |
