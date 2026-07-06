# addPointListToCurve()

Add many points to a curve in the IanniX score at once.

Each point is an (x, y, z) tuple. The two control-point lists shape the quadratic Bezier curves between points. Each control-point list must be either the same length as listPoints, or None to skip it.

## Parameters

Once an object `iannixout` has been created, you can use the following functions:

```python
iannixout.addPointListToCurve(curveID, listPoints)
```
```python
iannixout.addPointListToCurve(curveID, listPoints, listControlPoints1, listControlPoints2)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `curveID` | `int or str` | _required_ | The ID of the curve to add the points to. |
| `listPoints` | `list[tuple[float, float, float]]` | _required_ | The points to add, each an (x, y, z) tuple. |
| `listControlPoints1` | `list[tuple[float, float, float]]` | `None` | The first Bezier control point for each point, each a (cx1, cy1, cz1) tuple. Defaults to none. |
| `listControlPoints2` | `list[tuple[float, float, float]]` | `None` | The second Bezier control point for each point, each a (cx2, cy2, cz2) tuple. Defaults to none. |
