"""Fail-closed YAML loading and content identity for application artifacts."""

import hashlib
import json
import re
from pathlib import Path

import yaml


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently accepting the last approval."""


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ValueError("YAML keys must be unique strings")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)
# Keep ISO dates as strings for stable JSON hashes and consistent card contracts.
UniqueLoader.yaml_implicit_resolvers = {
    first: [(tag, rx) for tag, rx in entries if tag != "tag:yaml.org,2002:timestamp"]
    for first, entries in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml_text(text):
    try:
        return yaml.load(text, Loader=UniqueLoader)
    except yaml.YAMLError as exc:
        raise ValueError("Invalid YAML") from exc


def load_yaml(path):
    return load_yaml_text(Path(path).read_text(encoding="utf-8"))


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def card_hash(card):
    return digest(
        {k: v for k, v in card.items() if k not in {"approval", "user_confirmed", "verified"}}
    )


def read_cards(text, prefix, gate):
    data = load_yaml_text(text)
    if data is None:
        return {}
    if not isinstance(data, list):
        raise ValueError("Card document must be a YAML list")
    result = {}
    for card in data:
        if not isinstance(card, dict):
            raise ValueError("Each card must be an object")
        key = card.get("id")
        if not isinstance(key, str) or not re.fullmatch(rf"{prefix}-\d{{2,}}", key):
            raise ValueError(f"Invalid {prefix} card ID")
        if key in result:
            raise ValueError(f"Duplicate card ID: {key}")
        if type(card.get(gate)) is not bool:
            raise ValueError(f"{key}: {gate} must be a boolean")
        result[key] = card
    return result


def get_field(card, path):
    """Dot paths support objects/list indices, never expressions or attributes."""
    value = card
    for part in path.split("."):
        if isinstance(value, list) and part.isdigit():
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value[part]
        else:
            raise ValueError("Invalid evidence field path")
    return value


def project_path(root, relative):
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Artifact path escapes application directory")
    return path


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()
