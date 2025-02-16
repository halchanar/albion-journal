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
PROJECTFILE = "pyproject.toml"
try:
    with open(PROJECTFILE, "rb") as f:
        pyproject_data = tomllib.load(f)
except FileNotFoundError:
    print(f"{PROJECTFILE} not found and is required... exiting")
    sys.exit(1)
except tomllib.TOMLDecodeError as e:
    print(f"Error parsing {PROJECTFILE}: {e}")
    print("... exiting")
    sys.exit(1)

project_name = pyproject_data["project"]["name"]
project_version = pyproject_data["project"]["version"]

# Load configuration settings
CONFIGFILE = "journal_xtractor-config.yaml"
try:
    with open(CONFIGFILE, "r", encoding="ascii") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print(f"{CONFIGFILE} not found and is required... exiting")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error parsing {CONFIGFILE}: {e}")
    print("... exiting")
    sys.exit(1)

try:
    log_level = config["logging"]["level"]
    options = config["options"]
    current_file = options["current_file"]
    output_file = options["output_file"]
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
    with open(current_file, "r", encoding="utf-8") as f:
        journalData = json.load(f, object_pairs_hook=OrderedDict)
    if len(journalData.keys()) > 1:
        raise KeyError(f"{current_file} must contain only 1 key... exiting")
except FileNotFoundError:
    print(f"{current_file} not found and is required... exiting")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error parsing {current_file}: {e}")
    print("... exiting")
    sys.exit(1)
except IOError:
    print(f"An error occurred while reading the {current_file} file.")
    sys.exit(1)
except KeyError as e:
    print(e)
    sys.exit(2)

# Begin writing data to the appropriate output file.
# The output file will be overwritten each time this script runs.
journalFile = open(output_file, "w", encoding="utf-8")

# Define `journal.md` format
JOURNALMDBEGIN = """```tsx
const Journal = ({ reward }: { reward: string }) => {
  return (
    <JournalProvider reward={reward}>"""
CATEGORYBEGIN = ""
SUBCATEGORYBEGIN = ""
SUBCATEGORYHEADER = """              <Table responsive striped borderless hover dark>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th style={{ width: 500 }}>Reward</th>
                  </tr>
                </thead>
                <tbody>"""
ACHIEVEMENTBEGIN = "                  <Entry"
REQUIREMENTSBEGIN = """                    name={
                      <>"""
REQUIREMENTSHEADER = """                        <br />
                        <span className=\"text-muted\">"""
REQUIREMENTSEND = """                        </span>
                      </>
                    }"""
ACHIEVEMENTEND = "                  />"
SUBCATEGORYEND = """                </tbody>
              </Table>"""
CATEGORYEND = """            </AccordionBody>
          </AccordionItem>
        </UncontrolledAccordion>
      </Section>"""
JOURNALMDEND = """    </JournalProvider>
  );
};
```"""

print(JOURNALMDBEGIN, file=journalFile)

for relTag, relData in journalData.items():
    print(f"Creating journal.md using data for {relTag}...")
    print(f"Albion Online {relData['type']} - {relData['name']}")
    print(f"    first available on {relData['date']}")

    for categoryID, catData in relData["categories"].items():
        # Use HTML encoding consistent with `journal.md` format
        categoryID = html.escape(categoryID).replace("#x27", "apos")
        categoryName = html.escape(catData["title"]).replace("#x27", "apos")

        # Count achievements in all subcategories
        achievementCount = sum(len(subCatData["achievements"].values(
        )) for subCatData in catData["subcategories"].values())

        # Write category name with total achievement count in `journal.md` format
        print(CATEGORYBEGIN, file=journalFile)
        print(f"      {{/* {categoryName} */}}", file=journalFile)
        print("      <Section>", file=journalFile)
        print(
            f"        <UncontrolledAccordion id=\"{categoryID.lower()}\">", file=journalFile)
        print("          <AccordionItem>", file=journalFile)
        print(
            f"            <AccordionHeader targetId=\"{categoryID.lower()}\">", file=journalFile)
        print(
            f"              {categoryName} ({str(achievementCount)})", file=journalFile)
        print("            </AccordionHeader>", file=journalFile)
        print(
            f"            <AccordionBody accordionId=\"{categoryID.lower()}\">", file=journalFile)

        for subcategoryID, subCatData in catData["subcategories"].items():
            # Use HTML encoding consistent with `journal.md` format
            subcategoryID = html.escape(subcategoryID).replace("#x27", "apos")
            subcategoryName = html.escape(
                subCatData["title"]).replace("#x27", "apos")

            # Count achievements in this subcategory
            achievementCount = len(subCatData["achievements"].values())

            # Write subcategory name with achievement count in `journal.md` format
            print(SUBCATEGORYBEGIN, file=journalFile)
            print(f"              <h4>{subcategoryName} ({str(achievementCount)})</h4>",
                  file=journalFile)
            print(SUBCATEGORYHEADER, file=journalFile)

            for achievementID, achData in subCatData["achievements"].items():
                # Use HTML encoding consistent with `journal.md` format
                achievementID = html.escape(
                    achievementID).replace("#x27", "apos")
                achievementName = html.escape(
                    achData["title"]).replace("#x27", "apos")
                rewardID = html.escape(
                    achData["reward"]["id"]).replace("#x27", "apos")
                reward = html.escape(
                    achData["reward"]["title"]).replace("#x27", "apos")
                requirementsNote = achData["requirements"]["note"]
                requirementsList = achData["requirements"]["list"]
                # Use HTML encoding for all requirements
                for k, v in enumerate(requirementsList):
                    requirementsList[k] = html.escape(
                        v).replace("#x27", "apos")

                # Write achievement entry in `journal.md` format
                print(ACHIEVEMENTBEGIN, file=journalFile)
                print(
                    f"                    entryID=\"{achievementID}\"", file=journalFile)

                if requirementsList:
                    # Include requirements with certain achievements
                    print(REQUIREMENTSBEGIN, file=journalFile)
                    print(
                        f"                        {achievementName}", file=journalFile)
                    print(REQUIREMENTSHEADER, file=journalFile)
                    print(
                        f"                          {requirementsNote}", end="", file=journalFile)
                    print(*requirementsList, sep=", ", file=journalFile)
                    print(REQUIREMENTSEND, file=journalFile)
                else:
                    # Most achievements will not include their requirements
                    print(
                        f"                    name=\"{achievementName}\"", file=journalFile)

                print(
                    f"                    id=\"{rewardID}\"", file=journalFile)
                print(
                    f"                    title=\"{reward}\"", file=journalFile)
                print(ACHIEVEMENTEND, file=journalFile)

            print(SUBCATEGORYEND, file=journalFile)

        print(CATEGORYEND, file=journalFile)

print(JOURNALMDEND, file=journalFile)
journalFile.close()
