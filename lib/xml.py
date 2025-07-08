"""
Define super class to parse XML files from the Albion Online Data Project (AODP)
"""

import lib
import xml.etree.ElementTree as ET
from pathlib import Path


class AODP_XMLHandler:
    """
    Handles reading AODP XML data and serializing it as JSON
    """

    def __init__(self, xml_path: str | Path):
        """Initialize the handler with the XML path"""
        if not xml_path:
            raise ValueError("XML file path must be provided")
        # Check for valid XML file extension and existence
        try:
            if not lib.file_exists(xml_path):
                raise FileNotFoundError(f"XML file not found: {xml_path}")
            if lib.validate_file_extension(xml_path, ".xml"):
                pass
        except TypeError as e:
            raise TypeError(f"Invalid XML file: {e}") from e
        except ValueError as e:
            raise ValueError(f"Invalid XML file: {e}") from e
        self.xml_path = xml_path
        self.data = None

    def read(self):
        """Reads XML file and parses it into a dictionary"""
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        self.data = self._etree_to_dict(root)

    def _etree_to_dict(self, elem: ET.Element) -> dict:
        """Recursively converts an ElementTree element to a dictionary"""
        d = {elem.tag: {} if elem.attrib else None}
        children = list(elem)
        if children:
            dd = {}
            for dc in map(self._etree_to_dict, children):
                for k, v in dc.items():
                    if k in dd:
                        if not isinstance(dd[k], list):
                            dd[k] = [dd[k]]
                        dd[k].append(v)
                    else:
                        dd[k] = v
            d = {elem.tag: dd}
        if elem.attrib:
            d[elem.tag].update(("@" + k, v) for k, v in elem.attrib.items())
        if elem.text and elem.text.strip():
            text = elem.text.strip()
            if children or elem.attrib:
                if text:
                    d[elem.tag]["#text"] = text
            else:
                d[elem.tag] = text
        return d

    def get(self):
        """Return the parsed data"""
        return self.data

    def write(self, json_file: str):
        """Serializes the parsed XML data to a JSON file"""
        if self.data is None:
            raise ValueError("No data loaded. Use read() first.")
        return lib.create_json_file(self.data, json_file)
