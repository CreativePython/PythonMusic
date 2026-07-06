# setLength()

Set how long the note actually sounds.

Length is normally about 90% of the duration. Raise it toward the duration to make the note sound legato (smooth), or lower it to make it sound staccato (short).

## Parameters

Once an object `note` has been created, you can use the following function:

```python
note.setLength(length)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `length` | `int or float` | _required_ | The new sounding length, in the same units as duration. |
