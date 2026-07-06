# getPitchBend()

Return the note's pitch bend, the gap between its pitch and its exact frequency.

## Parameters

Once an object `note` has been created, you can use the following function:

```python
note.getPitchBend()
```

## Returns

`return pitchBend`

| Value | Type | Description |
|---|---|---|
| pitchBend | `int` | The bend, in pitch bend units from -8191 to 8192, where 0 means no bend. |
