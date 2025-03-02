"""
Create `journal.md` to facilitate publication on
[Albion Online Grind](https://albiononlinegrind.com/guides/albion-journal-guide).
"""

import lib


def validate_journal_data(journal_data):
    """Confirm Journal data is well-formed"""
    try:
        if len(journal_data["headers"]) != 4:
            raise ValueError(
                f"Journal data mismatch: {len(journal_data['headers'])} headers " +
                "but expected 4")
        elif len(journal_data["levels"]) != 3:
            raise ValueError(
                f"Journal data mismatch: {len(journal_data['levels'])} levels " +
                "but expected 3")
        elif journal_data["levels"][0] not in journal_data["data"].keys():
            raise KeyError(f"{journal_data['levels'][0]}")
    except TypeError as e:
        raise TypeError(f"Journal data mismatch: {e}") from e
    except KeyError as e:
        raise KeyError(f"Journal data mismatch: {e} not found") from e


def print_journal_headers(journal_data):
    """Display release information from Journal data"""
    try:
        validate_journal_data(journal_data)
    except KeyError as e:
        raise KeyError(e) from e
    except ValueError as e:
        raise ValueError(e) from e
    except TypeError as e:
        raise TypeError(e) from e

    print(
        f"Creating `journal.md` using data from {journal_data['data']['commit hash']}...")
    print(
        f"Albion Online {journal_data['data']['type']} - {journal_data['data']['name']}")
    print(f"    first available on {journal_data['data']['date']}")


def create_journal_text(journal_data, templates):
    """Create text in `journal.md` format from Journal data"""
    try:
        validate_journal_data(journal_data)
    except KeyError as e:
        raise KeyError(e) from e
    except ValueError as e:
        raise ValueError(e) from e
    except TypeError as e:
        raise TypeError(e) from e

    journal_text = templates["file_begin"]
    level_0 = journal_data["levels"][0]
    level_1 = journal_data["levels"][1]
    level_2 = journal_data["levels"][2]

    for category_id, category_data in journal_data["data"][level_0].items():
        # Use HTML encoding consistent with `journal.md` format
        category_id = lib.escape_html(category_id)
        category_name = lib.escape_html(category_data["title"])

        # Count achievements in all subcategories
        achievement_count = sum(len(subcat_data[level_2].values(
        )) for subcat_data in category_data[level_1].values())

        # Write category name with total achievement count in `journal.md` format
        template_input = {"categoryID": category_id.lower(), "categoryName": category_name,
                          "achievementCount": str(achievement_count)}
        journal_text = "\n".join([journal_text,
                                  templates["category_begin"].format(**template_input)])

        for subcat_data in category_data[level_1].values():
            # Use HTML encoding consistent with `journal.md` format
            subcategory_name = lib.escape_html(subcat_data["title"])

            # Count achievements in this subcategory
            achievement_count = len(subcat_data[level_2].values())

            # Write subcategory name with achievement count in `journal.md` format
            template_input = {"subcategoryName": subcategory_name,
                              "achievementCount": str(achievement_count)}
            journal_text = "\n".join([journal_text,
                                      templates["subcategory_begin"].format(**template_input)])

            for achievement_id, ach_data in subcat_data[level_2].items():
                # Use HTML encoding consistent with `journal.md` format
                achievement_id = lib.escape_html(achievement_id)
                achievement_name = lib.escape_html(ach_data["title"])
                reward_id = lib.escape_html(ach_data["reward"]["id"])
                reward = lib.escape_html(ach_data["reward"]["title"])
                requirements_note = ach_data["requirements"]["note"]
                requirements_list = ach_data["requirements"]["list"]
                # Use HTML encoding for all requirements
                for k, v in enumerate(requirements_list):
                    requirements_list[k] = lib.escape_html(v)

                # Write achievement entry in `journal.md` format
                template_input = {
                    "achievementID": achievement_id,
                    "achievementName": achievement_name,
                    "rewardID": reward_id,
                    "reward": reward,
                    "requirementsNote": requirements_note,
                    "requirementsList": ", ".join(requirements_list)
                }
                if requirements_list:
                    # Include requirements with certain achievements
                    journal_text = "\n".join([journal_text,
                                              templates["achievement_with_requirements"].format(
                                                  **template_input)])
                else:
                    # Most achievements will not include their requirements
                    journal_text = "\n".join([journal_text,
                                              templates["achievement"].format(**template_input)])

            journal_text = "\n".join(
                [journal_text, templates["subcategory_end"]])

        journal_text = "\n".join([journal_text, templates["category_end"]])

    journal_text = "\n".join([journal_text, templates["file_end"]])

    return journal_text
