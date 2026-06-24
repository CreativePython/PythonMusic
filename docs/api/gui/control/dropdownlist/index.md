# DropDownList

Create a drop-down list the user can pick items from.

## Creating a DropDownList

You can create a DropDownList using the following functions:

```python
dropdown = DropDownList()
```

```python
DropDownList(items, action, color)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `items` | `list[str]` | `[]` | The items to show, for example ["item1", "item2", "item3"]. |
| `action` | `function` | `None` | The function to call when an item is picked; it receives one parameter, the selected item as a string. |
| `color` | `Color` | `Color.LIGHT_GRAY` | The dropdown's background color. |

For example,

```python
dropdown = DropDownList(["item1", "item2", "item3"], itemSelected)
```

where `itemSelected` is a function which expects one parameter, the selected item (a string).

Once created, you can add it to a [Display](../../display/index.md) using the Display's [add()](../../display/add.md) function.

## Functions

Once a DropDownList has been created, the following functions are available:

| Function | Description |
|---|---|
| [`getColor()`](../../common/color/getColor.md) | Return the dropdown's background color. |
| [`setColor(color)`](../../common/color/setColor.md) | Set the dropdown's background color. |
| [`onAction()`](onAction.md) | Register a function to call when an item is picked. |

Additionally, the following common functions are available:

- [Position](../../common/index.md#position-functions)
- [Size](../../common/index.md#size-functions)
- [Visibility](../../common/index.md#visibility-functions)
- [Information](../../common/index.md#information-functions)
- [Hit Testing](../../common/index.md#hit-testing-functions)
- [Events](../../common/index.md#event-functions)