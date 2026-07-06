# Metronome

Keep time and call functions on the beat, at a set tempo and time signature.

Metronome objects are used to synchronize blocks of musical material (i.e., by making sure they start playing together), e.g., for live coding applications. It is very hard otherwise (you need a steady hand, and luck) to start things together at the exact same time. Of course, Metronome objects can be used for other things (e.g., GUI animation).

A metronome has a tempo (e.g., 60 BPM), and a time signature (e.g., 4/4).

A program may have several metronomes active at the same time.

## Creating a Metronome

You can create a Metronome using the following functions:

```python
Metronome()
```

```python
Metronome(tempo, timeSignature)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tempo` | `int` | `60` | The tempo, in beats per minute. |
| `timeSignature` | `list[int]` | `[4, 4]` | The time signature as [beats, beatValue], for example [4, 4] for 4/4. |

For example,

```python
metronome = Metronome()
```

## Functions

Once a Metronome `metronome` has been created, the following functions are available:

| Function | Description |
|---|---|
| [`start()`](start.md) | Start the metronome ticking. |
| [`stop()`](stop.md) | Stop the metronome ticking. |
| [`add(action)`](add.md) | Schedule a function for the metronome to call on a given beat. |
| [`remove(action)`](remove.md) | Remove a scheduled function from the metronome. |
| [`removeAll()`](removeAll.md) | Remove every scheduled function from the metronome. |
| [`getTempo()`](getTempo.md) | Return the metronome's tempo. |
| [`setTempo(tempo)`](setTempo.md) | Set the metronome's tempo. |
| [`getTimeSignature()`](getTimeSignature.md) | Return the metronome's time signature. |
| [`setTimeSignature(timeSignature)`](setTimeSignature.md) | Set the metronome's time signature. |
| [`soundOn()`](soundOn.md) | Play a sound on every metronome tick. |
| [`soundOff()`](soundOff.md) | Stop playing a sound on each metronome tick. |
| [`show()`](show.md) | Start printing the current beat number to the console on each tick. |
| [`hide()`](hide.md) | Stop printing the beat number to the console. |
