"""
Define class for Albion Online localization data
"""

from typing import Dict, Optional
from lib.xml import AODP_XMLHandler
from pathlib import Path


class Localization(AODP_XMLHandler):
    """
    Handler for Albion Online localization data
    """

    def __init__(self, xml_path: str | Path, locale: str = "EN-US"):
        """Initialize the handler with the XML path"""
        try:
            super().__init__(xml_path)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"{e}") from e
        except TypeError as e:
            raise TypeError(f"{e}") from e
        except ValueError as e:
            raise ValueError(f"{e}") from e
        self.localization_data: Dict[str, str] = {}
        self.locale = locale

    def _extract_translations(self):
        """Extract the localized translations from the Albion Online data"""
        translations: Dict[str, str] = {}
        for translation in self.data["tmx"]["body"]["tu"]:
            if isinstance(translation, dict) and "@tuid" not in translation:
                continue
            # Extract the translation key and value
            if not isinstance(translation, dict):
                continue
            if "@tuid" not in translation or "tuv" not in translation:
                continue
            # Process the translation
            lang = None
            key = translation["@tuid"]
            value = translation["tuv"]
            if isinstance(value, list):
                for item in value:
                    if (
                        isinstance(item, dict)
                        and "@{http://www.w3.org/XML/1998/namespace}lang" in item
                    ):
                        lang = item["@{http://www.w3.org/XML/1998/namespace}lang"]
                        if lang == self.locale:
                            value = item["seg"]
                            break
            elif (
                isinstance(value, dict)
                and "@{http://www.w3.org/XML/1998/namespace}lang" in value
            ):
                lang = value["@{http://www.w3.org/XML/1998/namespace}lang"]
                if lang != self.locale:
                    continue
                value = value["seg"]
            else:
                value = None
            if key and value:
                translations[key] = value
        return translations

    def read(self):
        super().read()
        self.localization_data = self._extract_translations()

    def get(self, key: str) -> Optional[str]:
        """Return the localized string for the given key, or None if not found"""
        return self.localization_data.get(key)

    def all(self) -> Dict[str, str]:
        """Return the entire localization dictionary"""
        return self.localization_data
