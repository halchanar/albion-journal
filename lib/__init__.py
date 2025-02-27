"""
Utility functions for journal_xtractor.py
"""

import tomllib
import html
import json
from collections import OrderedDict
import yaml
import git


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


def create_text_file(text_data, output_file):
    """Write UTF-8 text to file"""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            print(text_data, file=f)
    except IOError as e:
        raise IOError(
            f"An error occurred while writing the {output_file} file.") from e
    finally:
        f.close()


def create_json_file(json_data, json_file):
    """Write JSON data to file"""
    try:
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        raise IOError(
            f"An error occurred while writing the {json_file} file.") from e
    finally:
        f.close()


def load_git_repo(repo_dir, repo_url):
    """Load Git repository"""
    try:
        return git.Repo(repo_dir)
    except git.InvalidGitRepositoryError as e:
        raise ChildProcessError(f"Invalid repository: {e}") from e
    except git.NoSuchPathError as e:
        if repo_url:
            try:
                print(
                    f"Repository not found... attempting to clone from {repo_url}")
                git.Repo.clone_from(repo_url, repo_dir)
            except git.GitError as e2:
                raise ChildProcessError(
                    f"An error occurred while cloning from {repo_url}") from e2
            except IOError as e2:
                raise IOError(
                    f"An error occurred while cloning to {repo_dir}") from e2
        else:
            raise FileNotFoundError(f"{repo_dir} not found") from e


def checkout_git_repo(git_repo, repo_branch):
    """Checkout Git repository"""
    try:
        git_repo.git.checkout(repo_branch)
    except git.CheckoutError as e:
        raise ChildProcessError(
            f"An error occurred while checking out {repo_branch}") from e
    except TypeError as e:
        raise TypeError(f"{git_repo} is not a Git repository") from e
