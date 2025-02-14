#!/usr/bin/env python3
"""
Parse data files from the Albion Online Data Project (AODP) to extract achievements and rewards for
the Albion Journal. Store history of changes for later reference.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import git

# The AODP binary file dumps must be available for extraction.
# If the AODP dumps are not at the parent directory level, modify the `parseDir` variable below.
# https://github.com/ao-data/ao-bin-dumps
AODPBINDUMPSDIRNAME = "ao-bin-dumps"
JOURNALXMLFILE = "albionjournal.xml"
ITEMSXMLFILE = "items.xml"
MOBSXMLFILE = "mobs.xml"
LOCALIZATIONXMLFILE = "localization.xml"
currentDir = Path(__file__).parent
parseDir = currentDir.parent / AODPBINDUMPSDIRNAME

# Use GitPython to reference specific commits associated with each release.
# See `AORELEASES` below for the complete list.
repo = git.Repo(parseDir)

# This file will be overwritten each time this script runs.
HISTORYFILE = "albionjournal-history.json"

# This is the list of Albion Online releases, patches, and hotfixes
# since the Albion Journal was introduced.
AORELEASES = {
    "f1de4b24e81726c8c638d9708310bf2c4d273711": [
        "release", "Paths to Glory", "July 22, 2024"
    ],
    "8c3002ca0a757fe46ee8dcd5514b0be01166ac25": [
        "patch", "Paths to Glory Patch #1", "August 7, 2024"
    ],
    "5d2396c21f64123d6c66b32f55650d8dca8811a1": [
        "patch", "Paths to Glory Patch #2", "August 21, 2024"
    ],
    "ee92a1cd3c07db05d324e3ca8fbb0adcaffddd69": [
        "patch", "Paths to Glory Patch #3", "September 4, 2024"
    ],
    "49fa486b4ea45bdcd35a9f6aabb042d0396324a4": [
        "patch", "Paths to Glory Patch #4", "September 18, 2024"
    ],
    "70aa34b154fb0062289cbbc596dca6256043f245": [
        "release", "Horizons", "October 28, 2024"
    ],
    "160f7f5c087fa0a0118c7a8477e6a17caf22dc78": [
        "patch", "Horizons Patch #1", "November 6, 2024"
    ],
    "a6d1a19cebdb8263f41282a69b62020643b76123": [
        "patch", "Horizons Patch #2", "November 20, 2024"
    ],
    "d2dd1d559d37a75cc25b805b5e93ad415c2916a4": [
        "patch", "Horizons Patch #3", "November 27, 2024"
    ],
    "4c5495c8de5279e776b6f8e31d42b3dbff0072f2": [
        "patch", "Horizons Patch #4", "December 4, 2024"
    ],
    "87bba4cd76217c08c1142db0fe2c5c276640ff2b": [
        "patch", "Horizons Patch #5", "December 18, 2024"
    ],
    "44358f340b61e7640ef0ceae79bead7432352336": [
        "release", "Rogue Frontier", "February 3, 2025"
    ],
    "44e15edf86a20b055981ae962c968e358690424a": [
        "hotfix", "Rogue Frontier Hotfix #1", "February 5, 2025"
    ],
    "c9c9cac6c33de8a5e364354214cfa5ea37e2cd8a": [
        "patch", "Rogue Frontier Patch #1", "February 12, 2025"
    ]
}

# This is the data structure used to store the history.
"""
journalHistory = {
    "Tag1": [
        "release or patch or hotfix", "Name or Description", "Date", {
            "Category1": [
                "Category1 Name", {
                    "Subcategory1": [
                        "Subcategory1 Name", {
                            "Achievement1": [
                                "Achievement1 Name",
                                "Achievement1 Reward ID",
                                "Achievement1 Reward Title", [
                                    "Achievement1 Requirement1"
                                ]
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}
"""

# Define list of achievements to display their requirements (e.g., quest, creature, location)
# NOTE 1: There are quite a few of these to potentially display, so we're intentionally
#   choosing a subset of them for aesthetics.
# NOTE 2: Displaying these introduces significant complexity when parsing the various XML files,
#   so we must also specify how to handle special cases.
showRequirements = {
    "achievement list": [
        "SA_EXPEDITION_FINISH_ALL",
        "JOURNAL_PVE_EXPEDITION_FINISH_ALL_HARDCORE",
        "SA_PVE_TRACKING_HUNT_ALL",
        "JOURNAL_PVE_TRACKING_KILL_RARE_MOBS_GROUP_7",
        "JOURNAL_PVE_WORLDBOSS_KILL_T8_WORLDBOSSES_ALL",
        "JOURNAL_PVE_WORLDBOSS_KILL_WORLDBOSSES_IN_ALL_LOCATIONS",
        "SA_PVE_KILL_RD_ELITE_01",
        "JOURNAL_GATHERING_SKINNING_ANIMAL_ALL",
        "JOURNAL_GATHERING_SKINNING_LOOT_BABY_ALL",
        "JOURNAL_GATHERING_FISHING_CATCH_ALL",
        "SA_PVE_KILL_MINIGUARDIANS",
        "JOURNAL_GATHERING_CRITTERS_CRITTERS_UNIQUE_ALL",
        "SA_EXPLORATION_CITIES",
        "JOURNAL_EXPLORATION_CITIES_VISIT_REST_CITY_ALL",
        "JOURNAL_EXPLORATION_TRAVEL_RIDE_ADC_MOUNT",
        "JOURNAL_EXPLORATION_TRAVEL_RIDE_FW_ALL",
        "SA_PVE_MISTS_HUNTER",
        "JOURNAL_EXPLORATION_SMUGGLERS_VISIT_BLACKBANKS_08",
        "SA_FACTIONWARFARE_KILLBOSS_ALL"
    ],
    "tags to skip": ["alternative"],
    "include tier": [""],
    "include count": ["SA_FACTIONWARFARE_KILLBOSS_ALL"],
    "correct SBI naming mistakes": {
        "XML tag to match": {
            "attribute to swap out": [
                "ID_TO_SWAP_OUT"
            ],
            "attribute to swap in": [
                "ID_TO_SWAP_IN"
            ]
        },
        "item": {
            "name": [
                "ID_TO_SWAP_OUT"
            ],
            "namelocatag": [
                "ID_TO_SWAP_IN"
            ]
        },
        "DroppedByMob": {
            "name": [
                "T4_MOB_CRITTER_HIDE_COUGAR",
                "T8_MOB_CRITTER_HIDE_COUGAR"
            ],
            "namelocatag": [
                "@MOB_T4_MOB_CRITTER_HIDE_COUGAR",
                "@MOB_T8_MOB_CRITTER_HIDE_COUGAR"
            ]
        }
    }
}

# Limit the number of releases until testing is complete
AORELEASES = {
    "44e15edf86a20b055981ae962c968e358690424a": [
        "hotfix", "Rogue Frontier Hotfix #1", "February 5, 2025"
    ],
    "c9c9cac6c33de8a5e364354214cfa5ea37e2cd8a": [
        "patch", "Rogue Frontier Patch #1", "February 12, 2025"
    ]
}
journalHistory = {}

for relTag, relData in AORELEASES.items():
    relData.append({})
    journalHistory[relTag] = relData
    print(f"Processing data for {relTag}...")
    print(f"Albion Online {relData[0]} - {relData[1]}")
    print(f"    first available on {relData[2]}")

    # Checkout the commit hash associated with the release.
    repo.git.checkout(relTag)

    jtree = ET.parse(parseDir / JOURNALXMLFILE)
    jroot = jtree.getroot()

    itree = ET.parse(parseDir / ITEMSXMLFILE)
    iroot = itree.getroot()

    mtree = ET.parse(parseDir / MOBSXMLFILE)
    mroot = mtree.getroot()

    ltree = ET.parse(parseDir / LOCALIZATIONXMLFILE)
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

        journalHistory[relTag][3][categoryID] = [categoryName, {}]

        for subcategory in jroot.findall(".//*[@uniquename='" + categoryID + "']/subcategory"):
            # Determine localized subcategory name
            subcategoryID = subcategory.get('uniquename')
            subcategoryNameID = subcategory.get('displayname')
            subcategoryName = lroot.find(
                ".//*[@tuid='" + subcategoryNameID + "']/tuv/seg").text

            journalHistory[relTag][3][categoryID][1][subcategoryID] = [
                subcategoryName, {}]

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
                if achievementID in showRequirements["achievement list"]:
                    REQUIREMENTCOUNT = ""
                    for requirement in jroot.findall(".//*[@name='" + achievementID + "']//"):
                        REQUIREMENTID = ""
                        REQUIREMENTTIER = ""

                        # Skip any subelements that aren't applicable
                        if requirement.tag in showRequirements["tags to skip"]:
                            continue

                        # Handle special cases
                        # CASE 1: There are situations when a `gather` or `killmob` element
                        # includes the requirement, but it's children aren't applicable.
                        if (requirement.tag == "gather" and "DroppedByMob"
                                not in showRequirements["tags to skip"]):
                            showRequirements["tags to skip"].append(
                                "DroppedByMob")
                        elif (requirement.tag == "killmob" and "nameloca" in requirement.attrib and
                                "mobid" not in showRequirements["tags to skip"]):
                            showRequirements["tags to skip"].append("mobid")
                        # CASE 2: Only use the `count` attribute when we know we need it and
                        # requirements are within an `any` tag.
                        if (achievementID in showRequirements["include count"] and
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
                                    showRequirements["correct SBI naming mistakes"]
                                        ["item"]["name"]):
                                    correctionIndex = (
                                        showRequirements["correct SBI naming mistakes"]
                                        ["item"]["name"].index(requirement.get('name')))
                                    REQUIREMENTID = (showRequirements["correct SBI naming mistakes"]
                                                     ["item"]["namelocatag"][correctionIndex])
                                else:
                                    REQUIREMENTID = "@ITEMS_" + \
                                        requirement.get('name')
                            elif requirement.tag == "DroppedByMob":
                                if (requirement.get('name') in
                                    showRequirements["correct SBI naming mistakes"]
                                        ["DroppedByMob"]["name"]):
                                    correctionIndex = (
                                        showRequirements["correct SBI naming mistakes"]
                                        ["DroppedByMob"]["name"].index(requirement.get('name')))
                                    mobLookup = (showRequirements["correct SBI naming mistakes"]
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

                                if achievementID in showRequirements["include tier"]:
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
                    if "DroppedByMob" in showRequirements["tags to skip"]:
                        showRequirements["tags to skip"].remove("DroppedByMob")
                    elif "mobid" in showRequirements["tags to skip"]:
                        showRequirements["tags to skip"].remove("mobid")

                journalHistory[relTag][3][categoryID][1][subcategoryID][1][achievementID] = [
                    achievementName, rewardID, reward, requirementsList]

# Reset the repository to track the main branch.
repo.git.checkout("master")

# Write all the history data to the reference file.
try:
    with open(HISTORYFILE, "w", encoding="utf-8") as f:
        json.dump(journalHistory, f, indent=4, ensure_ascii=False)
except IOError:
    print(f"An error occurred while writing the {HISTORYFILE} file.")
