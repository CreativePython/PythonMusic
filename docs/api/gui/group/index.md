# Group

Bundle several GUI objects (including other groups!) so they move, turn, and scale together.

## Creating a Group

You can create a Group using the following functions:

```python
Group()
```

```python
Group(itemList)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `itemList` | `list[Drawable]` | `[]` | The objects to start the group with. |

For example,

```python
group = Group(itemList)
```

where `itemList` is a list of GUI objects.  Moving, resizing, and rotating the group also changes the items within it accordingly.

Once created, you can add it to a [Display](../display/index.md) using the Display's [add()](../display/add.md) function.

## Functions

Once a Group has been created, the following functions are available:

| Function | Description |
|---|---|
| [`add(item)`](add.md) | Add an object to the group. |
| [`remove(item)`](remove.md) | Remove an object from the group. |
| [`removeAll()`](removeAll.md) | Remove every object from the group. |
| [`getItems()`](getItems.md) | Return the objects currently in the group. |

### Layering GUI Objects

GUI objects within a Group are layered. Typically, the most recent object sits on top of the others (`order = 0`). You can change the order

| Function | Description |
|---|---|
| [`addOrder(item, order)`](addOrder.md) | Add an object to the group on a given layer. |
| [`getOrder(item)`](getOrder.md) | Return the layer an object sits on within the group. |
| [`setOrder(item, order)`](setOrder.md) | Move an object to a different layer within the group. |

### Manipulating the Group

Additionally, the following common functions are available:

- [Position](../common/index.md#position-functions)
- [Size](../common/index.md#size-functions)
- [Rotation](../common/index.md#rotation-functions)
- [Visibility](../common/index.md#visibility-functions)
- [Information](../common/index.md#information-functions)
- [Hit Testing](../common/index.md#hit-testing-functions)
- [Events](../common/index.md#event-functions)
