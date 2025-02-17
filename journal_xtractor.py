#!/usr/bin/env python3
"""
Parse data files from the Albion Online Data Project (AODP) to extract achievements and rewards for
the Albion Journal. Store history of changes for later reference. Create `journal.md` to facilitate
publication on [Albion Online Grind](https://albiononlinegrind.com/guides/albion-journal-guide).
"""

import sys
import lib

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
    journalData = lib.load_json_data(current_file)
    if len(journalData.keys()) > 1:
        raise KeyError(f"{current_file} must contain only 1 key... exiting")
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
except KeyError as e:
    print(e)
    sys.exit(2)

# Begin writing data to the appropriate output file.
# The output file will be overwritten each time this script runs.
journalFile = open(output_file, "w", encoding="utf-8")
print(templates["file_begin"], file=journalFile)

for relTag, relData in journalData.items():
    print(f"Creating journal.md using data for {relTag}...")
    print(f"Albion Online {relData['type']} - {relData['name']}")
    print(f"    first available on {relData['date']}")

    for categoryID, catData in relData["categories"].items():
        # Use HTML encoding consistent with `journal.md` format
        categoryID = lib.escape_html(categoryID)
        categoryName = lib.escape_html(catData["title"])

        # Count achievements in all subcategories
        achievementCount = sum(len(subCatData["achievements"].values(
        )) for subCatData in catData["subcategories"].values())

        # Write category name with total achievement count in `journal.md` format
        templateInput = {"categoryID": categoryID.lower(), "categoryName": categoryName,
                         "achievementCount": str(achievementCount)}
        print(templates["category_begin"].format(
            **templateInput), file=journalFile)

        for subcategoryID, subCatData in catData["subcategories"].items():
            # Use HTML encoding consistent with `journal.md` format
            subcategoryName = lib.escape_html(subCatData["title"])

            # Count achievements in this subcategory
            achievementCount = len(subCatData["achievements"].values())

            # Write subcategory name with achievement count in `journal.md` format
            templateInput = {"subcategoryName": subcategoryName,
                             "achievementCount": str(achievementCount)}
            print(templates["subcategory_begin"].format(
                **templateInput), file=journalFile)

            for achievementID, achData in subCatData["achievements"].items():
                # Use HTML encoding consistent with `journal.md` format
                achievementID = lib.escape_html(achievementID)
                achievementName = lib.escape_html(achData["title"])
                rewardID = lib.escape_html(achData["reward"]["id"])
                reward = lib.escape_html(achData["reward"]["title"])
                requirementsNote = achData["requirements"]["note"]
                requirementsList = achData["requirements"]["list"]
                # Use HTML encoding for all requirements
                for k, v in enumerate(requirementsList):
                    requirementsList[k] = lib.escape_html(v)

                # Write achievement entry in `journal.md` format
                templateInput = {
                    "achievementID": achievementID,
                    "achievementName": achievementName,
                    "rewardID": rewardID,
                    "reward": reward,
                    "requirementsNote": requirementsNote,
                    "requirementsList": ", ".join(requirementsList)
                }
                if requirementsList:
                    # Include requirements with certain achievements
                    print(templates["achievement_with_requirements"].format(
                        **templateInput), file=journalFile)
                else:
                    # Most achievements will not include their requirements
                    print(templates["achievement"].format(
                        **templateInput), file=journalFile)

            print(templates["subcategory_end"], file=journalFile)

        print(templates["category_end"], file=journalFile)

print(templates["file_end"], file=journalFile)
journalFile.close()
