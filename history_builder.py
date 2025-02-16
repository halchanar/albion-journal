#!/usr/bin/env python3
"""
Parse data files from the Albion Online Data Project (AODP) to extract achievements and rewards for
the Albion Journal. Store history of changes for later reference.
"""

import sys
import tomllib
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import json
import yaml
import git

# Load project settings
try:
    with open("pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
except FileNotFoundError:
    print("Configuration file not found")
    print("pyproject.toml is required")
    sys.exit(1)
except tomllib.TOMLDecodeError:
    print("Error parsing pyproject.toml")
    sys.exit(1)

project_name = pyproject_data["project"]["name"]
project_version = pyproject_data["project"]["version"]

# Load configuration settings
CONFIGFILE = "journal_xtractor-config.yaml"
try:
    with open(CONFIGFILE, "r", encoding="ascii") as f:
        config = yaml.safe_load(f)
except yaml.YAMLError as e:
    print(f"Error reading YAML file: {e}")
    sys.exit(1)
except FileNotFoundError:
    print("Configuration file not found")
    print(f"{CONFIGFILE} is required")
    sys.exit(1)

log_level = config["logging"]["level"]
options = config["options"]

# Display configuration settings
print(f"Running {project_name} version {project_version}")
print(f"Logging level: {log_level}")
print(f"Force rebuild: {options['force_rebuild']}")
print(f"Only create current file: {options['only_current']}")

# The AODP binary file dumps must be available for extraction. Either open an existing repository
# or clone it from the URL. If the AODP dumps are not at the parent directory level, modify the
# `parse_dir` variable below.
extract_source = config["extract_source"]
current_file = options["current_file"]
history_file = options["history_file"]
current_dir = Path(__file__).parent
parse_dir = current_dir.parent / extract_source["repo_dir"]

try:
    extract_repo = git.Repo(parse_dir)
except git.InvalidGitRepositoryError as e:
    print(f"Invalid repository: {e}")
    sys.exit(1)
except git.NoSuchPathError:
    print("Repository not found... attempting to clone from the URL")
    extract_repo = git.Repo.clone_from(extract_source["repo_url"], parse_dir)

# This is the data structure used to store the history.
journalHistory = {}
"""
journalHistory = {
    "Tag1": {
        "type": "release or patch or hotfix",
        "name": "Name or Description",
        "date": "Date",
        "categories": {
            "Category1": {
                "title": "Category1 Title",
                "subcategories": {
                    "Subcategory1": {
                        "title": "Subcategory1 Title",
                        "achievements": {
                            "Achievement1": {
                                "title": "Achievement1 Title",
                                "reward": {
                                    "id": "Achievement1 Reward ID",
                                    "title": "Achievement1 Reward Title"
                                },
                                "requirements": {
                                    "note": "Achievement1 Requirements Note",
                                    "list": [
                                        "Achievement1 Requirement1"
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
"""
ao_releases = config["ao_releases"]
show_requirements = config["show_requirements"]

# The `only_current` setting provides an efficient option.
# If enabled, reduce `ao_releases` to only the most recent.
if options["only_current"] is True:
    current_release_value = max(ao_releases.values(),
                                key=lambda x: datetime.fromisoformat(x["date"]))
    current_release_key = next(
        key for key, value in ao_releases.items() if value == current_release_value)
    ao_releases = {current_release_key: current_release_value}
# If disabled or missing, set expectation of extensive processing time.
else:
    print("NOTE: Processing ALL the Journal data (every release, patch, and minor correction)" +
          "will take a while .")

for relTag, relData in ao_releases.items():
    relData["categories"] = {}
    journalHistory[relTag] = relData
    print(f"Processing data for {relTag}...")
    print(f"Albion Online {relData['type']} - {relData['name']}")
    print(f"    first available on {relData['date']}")

    # Checkout the commit hash associated with the release.
    # See `ao_releases` in the configuration file for the complete list.
    extract_repo.git.checkout(relTag)

    jtree = ET.parse(parse_dir / extract_source["journal_xml_file"])
    jroot = jtree.getroot()

    itree = ET.parse(parse_dir / extract_source["items_xml_file"])
    iroot = itree.getroot()

    mtree = ET.parse(parse_dir / extract_source["mobs_xml_file"])
    mroot = mtree.getroot()

    ltree = ET.parse(parse_dir / extract_source["localization_xml_file"])
    lroot = ltree.getroot()

    for category in jroot.findall(".//category"):
        # Skip any categories that aren't applicable
        if category.get('hideinjournal') == "true":
            continue

        categoryID = category.get('uniquename')
        # Swap categories to match in-game order
        if categoryID == "GATHERING":
            category = jroot.find(".//category[@uniquename='ECONOMY']")
            categoryID = category.get('uniquename')
        elif categoryID == "ECONOMY":
            category = jroot.find(".//category[@uniquename='GATHERING']")
            categoryID = category.get('uniquename')

        # Determine localized category name
        categoryNameID = category.get('displayname')
        categoryName = lroot.find(
            ".//*[@tuid='" + categoryNameID + "']/tuv/seg").text

        journalHistory[relTag]["categories"][categoryID] = {
            "title": categoryName, "subcategories": {}}

        for subcategory in jroot.findall(".//*[@uniquename='" + categoryID + "']/subcategory"):
            # Determine localized subcategory name
            subcategoryID = subcategory.get('uniquename')
            subcategoryNameID = subcategory.get('displayname')
            subcategoryName = lroot.find(
                ".//*[@tuid='" + subcategoryNameID + "']/tuv/seg").text

            journalHistory[relTag]["categories"][categoryID]["subcategories"][subcategoryID] = {
                "title": subcategoryName, "achievements": {}}

            for achievement in jroot.findall(".//*[@uniquename='" + subcategoryID +
                                             "']/achievement"):
                # Determine localized achievement description
                achievementID = achievement.get('name')
                achievementNameID = "@" + achievementID + "_DESCRIPTION"
                achievementName = lroot.find(
                    ".//*[@tuid='" + achievementNameID + "']/tuv/seg").text
                rewardItem = achievement.get('rewarditem')

                # Replace ID suffix for certain reward items
                rewardID = re.sub("D1@[1-3]$", "1", rewardItem)
                # Remove enchantment designation when searching for reward items
                rewardItem = re.sub("@[1-3]$", "", rewardItem)

                # Determine reward item localized name
                # TBD: Create lookup function(s)
                rewardItemLookup = iroot.find(
                    ".//*[@uniquename='" + rewardItem + "']")
                if rewardItemLookup is None:
                    rewardItemLookup = iroot.find(
                        ".//*[@uniquename='" + rewardItem + "_TEMPLATE']")
                    if "namelocatag" in rewardItemLookup.attrib:
                        # Use `namelocatag` attribute if present
                        rewardItem = rewardItemLookup.get('namelocatag')
                        reward = lroot.find(
                            ".//*[@tuid='" + rewardItem + "']/tuv/seg").text
                    else:
                        # If `namelocatag` attribute is not present, prepend common usage for lookup
                        reward = lroot.find(
                            ".//*[@tuid='@ITEMS_" + rewardItem + "']/tuv/seg").text
                else:
                    if "namelocatag" in rewardItemLookup.attrib:
                        # Use `namelocatag` attribute if present
                        rewardItem = rewardItemLookup.get('namelocatag')
                        reward = lroot.find(
                            ".//*[@tuid='" + rewardItem + "']/tuv/seg").text
                    else:
                        # If `namelocatag` attribute is not present, prepend common usage for lookup
                        reward = lroot.find(
                            ".//*[@tuid='@ITEMS_" + rewardItem + "']/tuv/seg").text

                # Replace progress variables where present
                if "$$absoluteprogressmax$" in achievementName:
                    achievementName = achievementName.replace(
                        "$$absoluteprogressmax$", achievement.get('absoluteprogressmax'))

                # Replace description variables where present
                if "{0}" in reward:
                    rewardItemVariableLookup = lroot.find(
                        ".//*[@tuid='" + rewardItemLookup.get('descvariable0') + "']/tuv/seg").text
                    reward = reward.replace("{0}", rewardItemVariableLookup)
                if "{1}" in reward:
                    rewardItemVariableLookup = lroot.find(
                        ".//*[@tuid='" + rewardItemLookup.get('descvariable1') + "']/tuv/seg").text
                    reward = reward.replace("{1}", rewardItemVariableLookup)

                # Append reward amount where present
                amount = achievement.get('rewardamount')
                amount = "1" if amount is None else amount
                reward = reward if amount == "1" else reward + \
                    " (x" + amount + ")"

                # Determine requirements for certain achievements
                requirementsList = []
                REQUIREMENTSNOTE = ""
                if achievementID in show_requirements["achievements"]:
                    REQUIREMENTCOUNT = ""
                    for requirement in jroot.findall(".//*[@name='" + achievementID + "']//"):
                        REQUIREMENTID = ""
                        REQUIREMENTTIER = ""

                        # Skip any subelements that aren't applicable
                        if requirement.tag in show_requirements["skip_tags"]:
                            continue

                        # Handle special cases
                        # CASE 1: There are situations when a `gather` or `killmob` element
                        # includes the requirement, but it's children aren't applicable.
                        if (requirement.tag == "gather" and "DroppedByMob"
                                not in show_requirements["skip_tags"]):
                            show_requirements["skip_tags"].append(
                                "DroppedByMob")
                        elif (requirement.tag == "killmob" and "nameloca" in requirement.attrib and
                                "mobid" not in show_requirements["skip_tags"]):
                            show_requirements["skip_tags"].append("mobid")
                        # CASE 2: Only use the `count` attribute when we know we need it and
                        # requirements are within an `any` tag.
                        if (achievementID in show_requirements["include_count"] and
                                requirement.tag == "any" and "count" in requirement.attrib):
                            REQUIREMENTCOUNT = "Any " + \
                                requirement.get('count') + " of<br />"
                            REQUIREMENTSNOTE = REQUIREMENTCOUNT

                        if "nameloca" in requirement.attrib:
                            REQUIREMENTID = requirement.get('nameloca')
                        elif "namelocatag" in requirement.attrib:
                            REQUIREMENTID = requirement.get('namelocatag')
                        elif "itemid" in requirement.attrib:
                            REQUIREMENTID = "@ITEMS_" + \
                                requirement.get('itemid')
                        elif "name" in requirement.attrib:
                            if requirement.tag == "item":
                                if (requirement.get('name') in
                                    show_requirements["corrections"]
                                        ["item"]["name"]):
                                    correctionIndex = (
                                        show_requirements["corrections"]
                                        ["item"]["name"].index(requirement.get('name')))
                                    REQUIREMENTID = (show_requirements["corrections"]
                                                     ["item"]["namelocatag"][correctionIndex])
                                else:
                                    REQUIREMENTID = "@ITEMS_" + \
                                        requirement.get('name')
                            elif requirement.tag == "DroppedByMob":
                                if (requirement.get('name') in
                                    show_requirements["corrections"]
                                        ["DroppedByMob"]["name"]):
                                    correctionIndex = (
                                        show_requirements["corrections"]
                                        ["DroppedByMob"]["name"].index(requirement.get('name')))
                                    mobLookup = (show_requirements["corrections"]
                                                 ["DroppedByMob"]["namelocatag"][correctionIndex])
                                else:
                                    mobLookup = mroot.find(
                                        ".//*[@uniquename='" + requirement.get('name') +
                                        "']").get('namelocatag')

                                if mobLookup is not None:
                                    if lroot.find(".//*[@tuid='" + mobLookup +
                                                  "']/tuv/seg") is not None:
                                        REQUIREMENTID = mobLookup
                                    else:
                                        REQUIREMENTID = re.sub(
                                            "^@", "@MOB_", mobLookup)
                                else:
                                    REQUIREMENTID = "@MOB_" + \
                                        requirement.get('name')
                            elif requirement.tag == "mobid":
                                mobLookup = mroot.find(
                                    ".//*[@uniquename='" +
                                    requirement.get('name') + "']"
                                ).get('namelocatag')
                                if mobLookup is not None:
                                    if lroot.find(".//*[@tuid='" + mobLookup +
                                                  "']/tuv/seg") is not None:
                                        REQUIREMENTID = mobLookup
                                    else:
                                        REQUIREMENTID = re.sub(
                                            "^@", "@MOB_", mobLookup)
                                else:
                                    REQUIREMENTID = "@MOB_" + \
                                        requirement.get('name')

                                if achievementID in show_requirements["include_tier"]:
                                    REQUIREMENTTIER = "T" + \
                                        mroot.find(
                                            ".//*[@uniquename='" + requirement.get('name') +
                                            "']").get('tier') + " "

                            else:
                                REQUIREMENTID = requirement.get('name')

                        if REQUIREMENTID:
                            requirementAdd = REQUIREMENTTIER + lroot.find(
                                ".//*[@tuid='" + REQUIREMENTID + "']/tuv/seg").text
                            if not requirementsList or requirementsList[-1] != requirementAdd:
                                requirementsList.append(requirementAdd)

                    # Handle special skip cases
                    if "DroppedByMob" in show_requirements["skip_tags"]:
                        show_requirements["skip_tags"].remove("DroppedByMob")
                    elif "mobid" in show_requirements["skip_tags"]:
                        show_requirements["skip_tags"].remove("mobid")

                (journalHistory[relTag]["categories"]
                 [categoryID]["subcategories"][subcategoryID]["achievements"][achievementID]) = {
                     "title": achievementName,
                     "reward": {
                         "id": rewardID,
                         "title": reward
                     },
                     "requirements": {
                         "note": REQUIREMENTSNOTE,
                         "list": requirementsList
                     }
                }

# Reset the repository to track the main branch.
extract_repo.git.checkout(extract_source["repo_branch"])

# Write data from the latest release to the appropriate reference file.
if options["only_current"] is True:
    try:
        with open(current_file, "w", encoding="utf-8") as f:
            json.dump(journalHistory, f, indent=4, ensure_ascii=False)
    except IOError:
        print(f"An error occurred while writing the {current_file} file.")
        sys.exit(1)
    finally:
        f.close()
else:
    # Select the most recent if `journalHistory` has data from every release.
    current_release_value = max(journalHistory.values(),
                                key=lambda x: datetime.fromisoformat(x["date"]))
    current_release_key = next(
        key for key, value in journalHistory.items() if value == current_release_value)
    journalCurrent = {current_release_key: current_release_value}
    # Write data from the latest release to the appropriate reference file.
    try:
        with open(current_file, "w", encoding="utf-8") as f:
            json.dump(journalCurrent, f, indent=4, ensure_ascii=False)
    except IOError:
        print(f"An error occurred while writing the {current_file} file.")
        sys.exit(1)
    finally:
        f.close()
    # Write data from every release to the appropriate reference file.
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(journalHistory, f, indent=4, ensure_ascii=False)
    except IOError:
        print(f"An error occurred while writing the {history_file} file.")
        sys.exit(1)
    finally:
        f.close()
