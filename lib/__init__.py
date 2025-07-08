"""
Utility functions for journal_xtractor.py
"""

import tomllib
import html
import json
from collections import OrderedDict
import yaml
import git
from pathlib import Path


def file_exists(file_path: str | Path) -> bool:
    """Check if a file exists"""
    try:
        with open(file_path, "r", encoding="utf-8"):
            return True
    except FileNotFoundError:
        return False
    except IOError as e:
        raise IOError(f"An error occurred while checking {file_path}: {e}") from e


def validate_file_extension(file_path: str | Path, extension: str) -> bool:
    """Validate that the file has the correct extension"""
    if not isinstance(file_path, (str, Path)):
        raise TypeError(f"{file_path} must be a string or Path object")
    file_path = str(file_path)  # Ensure it's a string for extension check
    if not extension.startswith("."):
        raise ValueError("Extension must start with a '.'")
    extension = extension.lower()  # Normalize to lowercase for comparison
    if not file_path.endswith(extension):
        raise ValueError(f"File must have a {extension} extension")
    return True


def load_toml_data(toml_file: str | Path) -> dict:
    """Load data from TOML file"""
    try:
        if not file_exists(toml_file):
            raise FileNotFoundError(f"TOML file not found: {toml_file}")
        if validate_file_extension(toml_file, ".toml"):
            with open(toml_file, "rb") as f:
                return tomllib.load(f)
    except TypeError as e:
        raise TypeError(f"{e}") from e
    except ValueError as e:
        raise ValueError(f"{e}") from e
    except IOError as e:
        raise IOError(f"An error occurred while reading the {toml_file} file.") from e
    except tomllib.TOMLDecodeError as e:
        raise ChildProcessError(f"Error parsing {toml_file}: {e}") from e


def load_yaml_data(yaml_file: str | Path) -> dict:
    """Load data from YAML file"""
    try:
        if not file_exists(yaml_file):
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")
        if validate_file_extension(yaml_file, ".yaml") or validate_file_extension(
            yaml_file, ".yml"
        ):
            with open(yaml_file, "r", encoding="ascii") as f:
                return yaml.safe_load(f)
    except TypeError as e:
        raise TypeError(f"{e}") from e
    except ValueError as e:
        raise ValueError(f"{e}") from e
    except IOError as e:
        raise IOError(f"An error occurred while reading the {yaml_file} file.") from e
    except yaml.scanner.ScannerError as e:
        raise ChildProcessError(f"Error scanning {yaml_file}: {e}") from e
    except yaml.parser.ParserError as e:
        raise ChildProcessError(f"Error parsing {yaml_file}: {e}") from e
    except yaml.YAMLError as e:
        raise ChildProcessError(f"Error parsing {yaml_file}: {e}") from e


def load_json_data(json_file: str | Path) -> OrderedDict:
    """Load data from JSON file and maintain original order"""
    try:
        if not file_exists(json_file):
            raise FileNotFoundError(f"JSON file not found: {json_file}")
        if validate_file_extension(json_file, ".json"):
            with open(json_file, "r", encoding="utf-8") as f:
                return json.load(f, object_pairs_hook=OrderedDict)
    except TypeError as e:
        raise TypeError(f"{e}") from e
    except ValueError as e:
        raise ValueError(f"{e}") from e
    except IOError as e:
        raise IOError(f"{e}") from e
    except json.JSONDecodeError as e:
        raise ChildProcessError(f"Error parsing {json_file}: {e}") from e
    except IOError as e:
        raise IOError(f"An error occurred while reading the {json_file} file.") from e


def escape_html(text_to_escape: str) -> str:
    """Use built-in HTML escape and replace apostrophe hex code with id"""
    return html.escape(text_to_escape).replace("#x27", "apos")


def create_text_file(text_data: str, output_file: str | Path):
    """Write UTF-8 text to file"""
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            print(text_data, file=f)
    except IOError as e:
        raise IOError(f"An error occurred while writing the {output_file} file.") from e
    finally:
        f.close()


def create_json_file(json_data: object, json_file: str | Path):
    """Create a JSON file from the provided data"""
    try:
        if validate_file_extension(json_file, ".json"):
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"An error occurred while writing the {json_file} file.") from e
    finally:
        f.close()


def load_git_repo(repo_dir: str | Path, repo_url: str = None) -> git.Repo:
    """Load Git repository"""
    if not repo_dir.endswith("/"):
        repo_dir += "/"
    if not file_exists(repo_dir):
        if repo_url is None:
            raise FileNotFoundError(f"Repository directory not found: {repo_dir}")
    try:
        return git.Repo(repo_dir)
    except TypeError as e:
        raise TypeError(f"{e}") from e
    except ValueError as e:
        raise ValueError(f"{e}") from e
    except IOError as e:
        raise IOError(f"{e}") from e
    except git.InvalidGitRepositoryError as e:
        raise ChildProcessError(f"Invalid repository: {e}") from e
    except git.NoSuchPathError as e:
        if repo_url:
            try:
                print(f"Repository not found... attempting to clone from {repo_url}")
                git.Repo.clone_from(repo_url, repo_dir)
            except git.GitError as e2:
                raise ChildProcessError(
                    f"An error occurred while cloning from {repo_url}"
                ) from e2
            except IOError as e2:
                raise IOError(f"An error occurred while cloning to {repo_dir}") from e2
        else:
            raise FileNotFoundError(f"{repo_dir} not found") from e


def checkout_git_repo(git_repo: git.Repo, repo_branch: str):
    """Checkout Git repository"""
    try:
        git_repo.git.checkout(repo_branch)
    except git.CheckoutError as e:
        raise ChildProcessError(
            f"An error occurred while checking out {repo_branch}"
        ) from e
    except TypeError as e:
        raise TypeError(f"{git_repo} is not a Git repository") from e
