# Music Library

```python
from music import *
```

To simplify making music, the music library defines many musical parameters and functions.

**NOTE:** The first time you import `music`, PythonMusic will ask to download a high-quality soundfont (FluidR3 G2-2.sf2) for you.  This is necessary to play high quality MIDI sounds, and only needs to happen once.

| Contents | Description |
|---|---|
| [Music Constants](constants/index.md) | Useful constants for music, such as pitch, duration, and more.  |
| [Transcription](transcription/index.md) | Musical material objects: [Note](transcription/note/index.md), [Phrase](transcription/phrase/index.md), [Part](transcription/part/index.md), and [Score](transcription/score/index.md). |
| [Composition](composition/index.md) | Functions to help [read](composition/read/index.md), [write](composition/write/index.md), [view](composition/view/index.md), and [modify](composition/mod/index.md) musical material. |
| [Performance](performance/index.md) | Musical classes for creating [GUI](../gui/index.md), [OSC](../osc/index.md), or [Midi](../midi/index.md) instruments. |
| [Play](play/index.md) | Functions to play sounds through MIDI synthesizer. |
| [Pitch and Frequency](pitch.md) | Functions to translate pitch to frequency, and vice-versa. |
| [Microtonality](microtonality.md) | Creating pitches between standard semitones. |
