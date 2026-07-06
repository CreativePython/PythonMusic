# addPointToCurve()

Add a point to a curve in the IanniX score.

The control points shape a quadratic Bezier curve between this point and the previous point on the curve.

## Parameters

Once an object `iannixout` has been created, you can use the following functions:

```python
iannixout.addPointToCurve(curveID)
```
```python
iannixout.addPointToCurve(curveID, x, y, z, cx1, cy1, cz1, cx2, cy2, cz2)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `curveID` | `int or str` | _required_ | The ID of the curve to add the point to. |
| `x` | `float` | `0.0` | The point's x coordinate. |
| `y` | `float` | `0.0` | The point's y coordinate. |
| `z` | `float` | `0.0` | The point's z coordinate. |
| `cx1` | `float` | `0.0` | The x coordinate of the first Bezier control point. |
| `cy1` | `float` | `0.0` | The y coordinate of the first Bezier control point. |
| `cz1` | `float` | `0.0` | The z coordinate of the first Bezier control point. |
| `cx2` | `float` | `0.0` | The x coordinate of the second Bezier control point. |
| `cy2` | `float` | `0.0` | The y coordinate of the second Bezier control point. |
| `cz2` | `float` | `0.0` | The z coordinate of the second Bezier control point. |
