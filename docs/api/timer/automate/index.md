# Automate

PythonMusic supports automation through the [Automate.add()](add.md) function.

Automate drives repeated calls (animating graphics, sweeping a volume or filter, stepping through data, and so on) from a single master timer, so every effect stays in sync. Automation starts as soon as the first function is loaded, and its rate is measured in frames per second.

For example:

```python title="randomlyMovingCircle.py"
--8<-- "examples/_snippets/randomlyMovingCircle.py"
```

For more complex automation, see the [Timer](../timer/index.md) class.

## Creating an Automation

Automate is a static utility; you don't instantiate it like other objects.  Call its methods on the class itself.  For example,

```python
Automate.add(moveCircle)
```

## Functions

The following Automate functions are always available:

| Function | Description |
|---|---|
| [`add(action)`](add.md) | Calls a function repeatedly based on automation rate (see [setRate()](setRate.md)). |
| [`remove(action)`](remove.md) | Stop calling a registered function. |
| [`resume()`](resume.md) | Resume automation after a pause. |
| [`pause()`](pause.md) | Pause automation. |
| [`getRate()`](getRate.md) | Return how often automation runs.  Default is 60 times per second. |
| [`setRate()`](setRate.md) | Set how often automation runs. |
| [`addWithValues(action, values)`](addWithValues.md) | Step a function through a list of values, evenly spaced over time. |
| [`addWithTimedValues(action, values, times)`](addWithTimedValues.md) | Step a function through a list of values, each delivered at its own time. |
