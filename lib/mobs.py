"""
Define class for Albion Online mobs data
"""

from typing import Dict
from lib.xml import AODP_XMLHandler


class Mobs(AODP_XMLHandler):
    """
    Handler for Albion Online mobs data structure
    """

    def __init__(self, xml_path):
        """Initialize the handler with the XML path"""
        super().__init__(xml_path)
        self.mobs_data = None

    def read(self) -> bool:
        """Read the XML file and parse it into a dictionary"""
        super().read()
        self.mobs_data = self.data
        return self.mobs_data is not None

    def get(self):
        """Return the parsed Albion Online mobs data"""
        return self.mobs_data

    def localize(self, localization_data: Dict[str, str]):
        """Localize the Albion Online mobs data with provided translations"""
        if not self.mobs_data or "Mobs" not in self.mobs_data:
            raise ValueError(
                "Mobs data must be loaded before localization. Use read() first."
            )
        if not localization_data or not isinstance(localization_data, dict):
            raise ValueError("Localization data must be provided as a dictionary.")

        def recursive_localize(obj):
            if isinstance(obj, dict):
                if "@uniquename" in obj:
                    mob_id = obj.get("@uniquename")
                    if (
                        mob_namelocatag := obj.get("@namelocatag")
                    ) is not None and mob_namelocatag in localization_data:
                        obj["title"] = localization_data[mob_namelocatag]
                    elif "@MOB_" + mob_id in localization_data:
                        obj["title"] = localization_data["@MOB_" + mob_id]
                    else:
                        obj["title"] = "Unknown Mob"
                for v in obj.values():
                    recursive_localize(v)
            elif isinstance(obj, list):
                for entry in obj:
                    recursive_localize(entry)

        recursive_localize(self.mobs_data["Mobs"])

    def mob(self, mob_id: str) -> Dict:
        """Get mob data by mob ID, recursively searching for '@uniquename'."""
        if not self.mobs_data or "Mobs" not in self.mobs_data:
            raise ValueError(
                "Mobs data must be loaded before retrieving mobs. Use read() first."
            )

        def recursive_search(obj):
            if isinstance(obj, dict):
                if "@uniquename" in obj and obj["@uniquename"] == mob_id:
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

        return recursive_search(self.mobs_data["Mobs"])

    def tag(self, mob: dict) -> str:
        """Get localization tag for mob."""
        # Use @namelocatag if it exists
        if "@namelocatag" in mob:
            return mob["@namelocatag"]
        else:
            return "@MOB_" + mob["@uniquename"]
