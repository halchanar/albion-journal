"""
Define class for Albion Online items data
"""

from typing import Dict
from lib.xml import AODP_XMLHandler


class Items(AODP_XMLHandler):
    """
    Handler for Albion Online items data structure
    """

    def __init__(self, xml_path):
        """Initialize the handler with the XML path"""
        super().__init__(xml_path)
        self.items_data = None

    def read(self) -> bool:
        """Read the XML file and parse it into a dictionary"""
        super().read()
        self.items_data = self.data
        return self.items_data is not None

    def get(self):
        """Return the parsed Albion Online items data"""
        return self.items_data

    def localize(self, localization_data: Dict[str, str]):
        """Localize the Albion Online items data with provided translations"""
        if not self.items_data or "items" not in self.items_data:
            raise ValueError(
                "Items data must be loaded before localization. Use read() first."
            )
        if not localization_data or not isinstance(localization_data, dict):
            raise ValueError("Localization data must be provided as a dictionary.")

        def recursive_localize(obj):
            if isinstance(obj, dict):
                if "@uniquename" in obj:
                    item_id = obj.get("@uniquename")
                    if (
                        item_namelocatag := obj.get("@namelocatag")
                    ) is not None and item_namelocatag in localization_data:
                        obj["title"] = localization_data[item_namelocatag]
                    elif "@ITEMS_" + item_id in localization_data:
                        obj["title"] = localization_data["@ITEMS_" + item_id]
                    else:
                        obj["title"] = "Unknown Item"
                for v in obj.values():
                    recursive_localize(v)
            elif isinstance(obj, list):
                for entry in obj:
                    recursive_localize(entry)

        recursive_localize(self.items_data["items"])

    def item(self, item_id: str) -> Dict:
        """Get item data by item ID, recursively searching for '@uniquename'."""
        if not self.items_data or "items" not in self.items_data:
            raise ValueError(
                "Items data must be loaded before retrieving items. Use read() first."
            )

        def recursive_search(obj):
            if isinstance(obj, dict):
                if "@uniquename" in obj:
                    if (
                        obj["@uniquename"] == item_id
                        or obj["@uniquename"] == item_id + "_TEMPLATE"
                    ):
                        return obj
                for v in obj.values():
                    result = recursive_search(v)
                    if result is not None:
                        return result
            elif isinstance(obj, list):
                for entry in obj:
                    result = recursive_search(entry)
                    if result is not None:
                        return result
            return None

        return recursive_search(self.items_data["items"])

    def tag(self, item: dict) -> str:
        """Get localization tag for item."""
        # Use @namelocatag if it exists
        if "@namelocatag" in item:
            return item["@namelocatag"]
        else:
            return "@ITEMS_" + item["@uniquename"]
