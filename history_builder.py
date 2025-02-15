#!/usr/bin/env python3
"""
Parse data files from the Albion Online Data Project (AODP) to extract achievements and rewards for
the Albion Journal. Store history of changes for later reference.
"""

import tomllib
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import yaml
import git

# Load project settings
try:
    with open("pyproject.toml", "rb") as f:
        pyproject_data = tomllib.load(f)
except FileNotFoundError:
    print("pyproject.toml not found")
except tomllib.TOMLDecodeError:
    print("Error parsing pyproject.toml")

project_name = pyproject_data["project"]["name"]
project_version = pyproject_data["project"]["version"]

# Load configuration settings
CONFIGFILE = "config_xtractor.yaml"
try:
    with open(CONFIGFILE, "r", encoding="ascii") as f:
        config = yaml.safe_load(f)
except yaml.YAMLError as e:
    print(f"Error reading YAML file: {e}")
except FileNotFoundError:
    print("Configuration file not found")

log_level = config["logging"]["level"]
options = config["options"]

# Display configuration settings
print(f"Running {project_name} version {project_version}")
print(f"Logging level: {log_level}")
print(f"Force rebuild: {options['force_rebuild']}")

# The AODP binary file dumps must be available for extraction.
# If the AODP dumps are not at the parent directory level, modify the `parse_dir` variable below.
extract_source = config["extract_source"]
history_file = options["history_file"]
current_dir = Path(__file__).parent
parse_dir = current_dir.parent / extract_source["dir_name"]

# Use GitPython to switch to the specific commit associated with each release.
# See `ao_releases` in the configuration file for the complete list.
repo = git.Repo(parse_dir)
ao_releases = config["ao_releases_test"]
show_requirements = config["show_requirements"]

# This is the data structure used to store the history.
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
                                "requirements": [
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
"""

journalHistory = {}

for relTag, relData in ao_releases.items():
    if options["force_rebuild"] is False:
        break

    relData["categories"] = {}
    journalHistory[relTag] = relData
    print(f"Processing data for {relTag}...")
    print(f"Albion Online {relData['type']} - {relData['name']}")
    print(f"    first available on {relData['date']}")

    # Checkout the commit hash associated with the release.
    repo.git.checkout(relTag)

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
                     "requirements": requirementsList
                }

# Reset the repository to track the main branch.
repo.git.checkout("master")

# Write all the history data to the reference file.
try:
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(journalHistory, f, indent=4, ensure_ascii=False)
except IOError:
    print(
        f"An error occurred while writing the {history_file} file.")
