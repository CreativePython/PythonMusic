# select()

Open a color-selection dialog and return the color the user picks.

## Parameters

`Color.select()` is a static utility. Call it on the `Color` class itself, for example:

```python
Color.select()
```
```python
Color.select(red, green, blue)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `red` | `int` | `255` | The red component the dialog starts on, from 0 to 255. |
| `green` | `int` | `255` | The green component the dialog starts on, from 0 to 255. |
| `blue` | `int` | `255` | The blue component the dialog starts on, from 0 to 255. |

## Returns

`return red, green, blue`

| Value | Type | Description |
|---|---|---|
| red | `int` | The chosen red component, from 0 to 255. |
| green | `int` | The chosen green component, from 0 to 255. |
| blue | `int` | The chosen blue component, from 0 to 255. |
