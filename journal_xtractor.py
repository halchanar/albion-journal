#!/usr/bin/env python3
"""
Parse data files from the Albion Online Data Project (AODP) to extract achievements and rewards for
the Albion Journal. Store history of changes for later reference. Create `journal.md` to facilitate
publication on [Albion Online Grind](https://albiononlinegrind.com/guides/albion-journal-guide).
"""

import sys
import tomllib
import html
import json
from collections import OrderedDict
import yaml

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
config_settings = f"""Running {project_name} version {project_version}
Logging level: {log_level}
Force rebuild: {options["force_rebuild"]}
Only create current file: {options["only_current"]}"""
print(config_settings)

# Load data from the latest release.
current_file = options["current_file"]
try:
    with open(current_file, "r", encoding="utf-8") as f:
        journalData = json.load(f, object_pairs_hook=OrderedDict)
    if len(journalData.keys()) > 1:
        raise KeyError("Too many keys, expected 1")
except FileNotFoundError:
    print("Data file not found")
    print(f"{current_file} is required")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Data file {current_file} does not contain valid JSON")
    sys.exit(1)
except IOError:
    print(f"An error occurred while reading the {current_file} file.")
    sys.exit(1)
except KeyError as e:
    print(e)
    sys.exit(2)

# Begin writing data to the appropriate output file.
# The output file will be overwritten each time this script runs.
output_file = options["output_file"]
journalFile = open(output_file, "w", encoding="utf-8")

# Write file header in `journal.md` format
print("```tsx", file=journalFile)
print(
    "const Journal = ({ reward }: { reward: string }) => {", file=journalFile)
print("  return (", file=journalFile)
print("    <JournalProvider reward={reward}>", file=journalFile)

for relTag, relData in journalData.items():
    print(f"Creating journal.md using data for {relTag}...")
    print(f"Albion Online {relData['type']} - {relData['name']}")
    print(f"    first available on {relData['date']}")

    for categoryID, catData in relData["categories"].items():
        categoryName = catData["title"]

        # Count achievements in all subcategories
        achievementCount = sum(len(subCatData["achievements"].values(
        )) for subCatData in catData["subcategories"].values())

        # Write category name with total achievement count in `journal.md` format
        print("", file=journalFile)
        print("      {/* " + categoryName + " */}", file=journalFile)
        print("      <Section>", file=journalFile)
        print("        <UncontrolledAccordion id=\"" +
              categoryID.lower() + "\">", file=journalFile)
        print("          <AccordionItem>", file=journalFile)
        print("            <AccordionHeader targetId=\"" +
              categoryID.lower() + "\">", file=journalFile)
        print("              " + categoryName +
              " (" + str(achievementCount) + ")", file=journalFile)
        print("            </AccordionHeader>", file=journalFile)
        print("            <AccordionBody accordionId=\"" + categoryID.lower() + "\">",
              file=journalFile)

        for subcategoryID, subCatData in catData["subcategories"].items():
            subcategoryName = subCatData["title"]

            # Count achievements in this subcategory
            achievementCount = len(subCatData["achievements"].values())

            # Write subcategory name with achievement count in `journal.md` format
            print("", file=journalFile)
            print("              <h4>" + subcategoryName + " (" + str(achievementCount) + ")</h4>",
                  file=journalFile)
            print("              <Table responsive striped borderless hover dark>",
                  file=journalFile)
            print("                <thead>", file=journalFile)
            print("                  <tr>", file=journalFile)
            print("                    <th>Name</th>", file=journalFile)
            print(
                "                    <th style={{ width: 500 }}>Reward</th>", file=journalFile)
            print("                  </tr>", file=journalFile)
            print("                </thead>", file=journalFile)
            print("                <tbody>", file=journalFile)

            for achievementID, achData in subCatData["achievements"].items():
                achievementName = achData["title"]
                rewardID = achData["reward"]["id"]
                reward = achData["reward"]["title"]
                requirementsNote = achData["requirements"]["note"]
                requirementsList = achData["requirements"]["list"]

                # Write achievement entry in `journal.md` format
                print("                  <Entry", file=journalFile)
                print("                    entryID=\"" +
                      html.escape(achievementID).replace("#x27", "apos") + "\"", file=journalFile)

                # Use HTML encoding for all requirements
                for k, v in enumerate(requirementsList):
                    requirementsList[k] = html.escape(
                        v).replace("#x27", "apos")

                if requirementsList:
                    # Include requirements with certain achievements
                    print("                    name={", file=journalFile)
                    print("                      <>", file=journalFile)
                    print("                        " +
                          html.escape(achievementName).replace("#x27", "apos"), file=journalFile)
                    print("                        <br />", file=journalFile)
                    print(
                        "                        <span className=\"text-muted\">", file=journalFile)
                    print("                          " +
                          requirementsNote, end="", file=journalFile)
                    print(*requirementsList, sep=", ", file=journalFile)
                    print("                        </span>", file=journalFile)
                    print("                      </>", file=journalFile)
                    print("                    }", file=journalFile)
                else:
                    # Most achievements will not include their requirements
                    print("                    name=\"" +
                          html.escape(achievementName).replace(
                              "#x27", "apos") + "\"", file=journalFile)

                # Write achievement remaining detail and end tag in `journal.md` format
                print("                    id=\"" +
                      rewardID + "\"", file=journalFile)
                print("                    title=\"" +
                      reward + "\"", file=journalFile)
                print("                  />", file=journalFile)

            # Write subcategory end tags in `journal.md` format
            print("                </tbody>", file=journalFile)
            print("              </Table>", file=journalFile)

        # Write category end tags in `journal.md` format
        print("            </AccordionBody>", file=journalFile)
        print("          </AccordionItem>", file=journalFile)
        print("        </UncontrolledAccordion>", file=journalFile)
        print("      </Section>", file=journalFile)

# Write file footer in `journal.md` format
print("    </JournalProvider>", file=journalFile)
print("  );", file=journalFile)
print("};", file=journalFile)
print("```", file=journalFile)

journalFile.close()
