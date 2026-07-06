# getLength()

Return how long the note actually sounds.

Duration is the note's written value; length is how long it actually sounds, normally about 90% of the duration so notes sound separate.

## Parameters

Once an object `note` has been created, you can use the following function:

```python
note.getLength()
```

## Returns

`return length`

| Value | Type | Description |
|---|---|---|
| length | `int or float` | The sounding length, in the same units as duration. |
