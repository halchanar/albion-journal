"""
Utility functions for journal_xtractor.py
"""

import tomllib
import html
import json
from collections import OrderedDict
import yaml


def load_toml_data(toml_file):
    """Load data from TOML file"""
    try:
        with open(toml_file, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"{toml_file} not found") from e
    except tomllib.TOMLDecodeError as e:
        raise ChildProcessError(f"Error parsing {toml_file}: {e}") from e


def load_yaml_data(yaml_file):
    """Load data from YAML file"""
    try:
        with open(yaml_file, "r", encoding="ascii") as f:
            return yaml.safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"{yaml_file} not found") from e
    except yaml.YAMLError as e:
        raise ChildProcessError(f"Error parsing {yaml_file}: {e}") from e


def load_json_data(json_file):
    """Load data from JSON file and maintain original order"""
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f, object_pairs_hook=OrderedDict)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"{json_file} not found") from e
    except json.JSONDecodeError as e:
        raise ChildProcessError(f"Error parsing {json_file}: {e}") from e
    except IOError as e:
        raise IOError(
            f"An error occurred while reading the {json_file} file.") from e


def escape_html(text_to_escape):
    """Use built-in HTML escape and replace apostrophe hex code with id"""
    return html.escape(text_to_escape).replace("#x27", "apos")
