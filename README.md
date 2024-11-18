# Albion Journal Guide

Hey Adventurers, are you interested in helping us add rewards for the list of entries for Albion Journal? Well, that's your chance. We are looking for contributors to help us add rewards to the list of entries for Albion Journal. If interested, please check out the GitHub repository and make a Pull Request.

We appreciate your help!

## Contributions

* Edit [journal.md](/journal.md) file
* Add or edit an entry
```jsx
<Entry
 reward={reward} // keep this part as it is
 name="Finish a T3 Solo Expedition" // quest description
 id="T3_SILVERBAG_NONTRADABLE" // reward item ID
 title="Journeyman's Bag of Silver" // reward item name
/>
```
  * You can find the item ID from [items.txt](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/items.txt).
* Commit your changes and push them to your fork
* Make a Pull Request to the main repository
