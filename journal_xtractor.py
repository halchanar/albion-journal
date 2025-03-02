#!/usr/bin/env python3
"""
Parse data files from the Albion Online Data Project (AODP) to extract achievements and rewards for
the Albion Journal. Store history of changes for later reference. Create `journal.md` to facilitate
publication on [Albion Online Grind](https://albiononlinegrind.com/guides/albion-journal-guide).
"""

import sys
import lib
from lib.guide import print_journal_headers
from lib.guide import create_journal_text

PROJECTFILE = "pyproject.toml"
CONFIGFILE = "journal_xtractor-config.yaml"

# Load project settings
try:
    pyproject_data = lib.load_toml_data(PROJECTFILE)
except FileNotFoundError as e:
    print(e)
    print(f"{PROJECTFILE} is required... exiting")
    sys.exit(1)
except ChildProcessError as e:
    print(e)
    print("... exiting")
    sys.exit(1)

project_name = pyproject_data["project"]["name"]
project_version = pyproject_data["project"]["version"]

# Load configuration settings
try:
    config = lib.load_yaml_data(CONFIGFILE)
    log_level = config["logging"]["level"]
    options = config["options"]
    current_file = options["current_file"]
    output_file = options["output_file"]
    templates = config["journal_md_templates"]
except FileNotFoundError as e:
    print(e)
    print(f"{CONFIGFILE} is required... exiting")
    sys.exit(1)
except ChildProcessError as e:
    print(e)
    print("... exiting")
    sys.exit(1)
except KeyError:
    print("Required configuration settings not found... exiting")
    sys.exit(2)

# Display configuration settings
config_settings = f"""
Running {project_name} version {project_version}
Logging level: {log_level}
"""
print(config_settings)

# Load data from the latest release.
try:
    journal_data = lib.load_json_data(current_file)
except FileNotFoundError as e:
    print(e)
    print(f"{current_file} is required... exiting")
    sys.exit(1)
except ChildProcessError as e:
    print(e)
    print("... exiting")
    sys.exit(1)
except IOError as e:
    print(e)
    sys.exit(1)

# Display release information and create `journal.md` content
try:
    print_journal_headers(journal_data)
    TEXT = create_journal_text(journal_data, templates)
except TypeError as e:
    print(e)
    sys.exit(2)
except KeyError as e:
    print(e)
    sys.exit(2)

# The output file will be overwritten each time this script runs.
try:
    lib.create_text_file(TEXT, output_file)
except IOError as e:
    print(e)
    sys.exit(1)
