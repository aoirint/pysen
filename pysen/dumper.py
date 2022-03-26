import configparser
import pathlib
from collections import OrderedDict
from typing import Any, Dict, Optional

import tomlkit
import tomlkit.items
from tomlkit.toml_document import TOMLDocument

from .setting import SettingFile
from .types import PRIMITIVE_TYPES, SEQUENCE_TYPES


def dump_toml(path: pathlib.Path, setting: SettingFile) -> None:
    document: TOMLDocument = tomlkit.document()
    if path.exists():
        with path.open("r") as f:
            document = tomlkit.loads(f.read())

    # NOTE(igarashi): TOMLDocument inherists Dict
    entry = setting.entries()
    for p, d in sorted(entry):
        updated = SettingFile.update_by_entry(document, p, d)
        if isinstance(updated, tomlkit.items.Table):
            updated.comment(
                "# automatically generated by pysen\n"
                "# pysen ignores and overwrites any modifications"
            )

    with path.open("w") as f:
        buf = tomlkit.dumps(document)
        f.write(buf)


def _repr_cfg(data: Any) -> Optional[str]:
    if data is None:
        return None
    elif isinstance(data, PRIMITIVE_TYPES):
        return str(data)
    elif isinstance(data, SEQUENCE_TYPES):
        items = sorted(_repr_cfg(x) for x in data)
        return ",".join(x for x in items if x is not None)
    else:
        raise RuntimeError(f"{type(data)} is not supported in cfg")


def dump_cfg(path: pathlib.Path, setting: SettingFile) -> None:
    flatten: Dict[str, Dict[str, Any]] = {}
    for p, d in setting.entries():
        if len(p) > 1:
            raise RuntimeError(
                "configparser cannot handle a section whose depth is more than 1"
            )
        flatten[p[0]] = d

    config = configparser.ConfigParser(allow_no_value=True)
    if path.exists():
        with path.open("r") as f:
            config.read_file(f)

    for p, d in sorted(flatten.items()):
        config[p] = OrderedDict()
        config.set(p, "# automatically generated by pysen", None)
        config.set(p, "# pysen ignores and overwrites any modifications", None)
        config[p].update(
            ((k, _repr_cfg(v)) for k, v in sorted(d.items()))  # type: ignore[misc]
        )

    with path.open("w") as f:
        config.write(f)


def dump(base_dir: pathlib.Path, fname: str, data: SettingFile) -> None:
    target_path = base_dir / fname
    ext = target_path.suffix
    if ext == ".toml":
        return dump_toml(target_path, data)
    elif ext == ".cfg" or ext == ".ini":
        return dump_cfg(target_path, data)
    else:
        raise RuntimeError(f"unknown extension: {ext}")
