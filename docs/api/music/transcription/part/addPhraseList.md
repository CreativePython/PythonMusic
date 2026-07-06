# addPhraseList()

Add several phrases to the part at once.

Any phrase with no set start time is placed at the end of the part.

## Parameters

Once an object `part` has been created, you can use the following function:

```python
part.addPhraseList(phraseList)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `phraseList` | `list[Phrase]` | _required_ | The phrases to add. |
