# addCursor()

Add a cursor to a curve in the IanniX score.

A cursor travels along its curve as the score plays.

## Parameters

Once an object `iannixout` has been created, you can use the following functions:

```python
iannixout.addCursor(curveID, cursorID)
```
```python
iannixout.addCursor(curveID, cursorID, offset)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `curveID` | `int or str` | _required_ | The ID of the curve to place the cursor on. |
| `cursorID` | `int or str` | _required_ | The ID to give the new cursor. |
| `offset` | `float` | `0.0` | How far along the curve to start the cursor, in seconds from the start of the curve. |
