# addCurve()

Add a new curve to the IanniX score.

The curve starts with no points. Add points to it with [addPointToCurve()](addPointToCurve.md) or [addPointListToCurve()](addPointListToCurve.md).

## Parameters

Once an object `iannixout` has been created, you can use the following function:

```python
iannixout.addCurve(curveID, x, y, z)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `curveID` | `int or str` | _required_ | The ID to give the new curve. |
| `x` | `float` | _required_ | The curve's x coordinate. |
| `y` | `float` | _required_ | The curve's y coordinate. |
| `z` | `float` | _required_ | The curve's z coordinate. |
