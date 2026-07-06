# onStop()

Set up a function to call when IanniX stops.

## Parameters

Once an object `iannixin` has been created, you can use the following function:

```python
iannixin.onStop(action)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `action` | `function` | _required_ | The function to call; it receives one parameter, the current time in seconds. |
