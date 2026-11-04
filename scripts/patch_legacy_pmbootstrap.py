#!/usr/bin/env python3
"""Adapt pmbootstrap 1.50.1 to apk 3's version and progress output.

The signed binary and APKINDEX package version must still match. Older apk
versions reported only the upstream version, while apk 3 also reports -rN.
Ignore only unrecognized progress messages; apk's exit status is still checked.
"""

import argparse
from pathlib import Path


OLD = 'if not version.startswith(f"{version_bin}-r"):'
NEW = 'if version_bin != version and not version.startswith(f"{version_bin}-r"):'
OLD_PROGRESS = "    cur = float(cur_tot[0])\n    tot = float(cur_tot[1])\n"
NEW_PROGRESS = (
    "    try:\n"
    "        cur = float(cur_tot[0])\n"
    "        tot = float(cur_tot[1])\n"
    "    except ValueError:\n"
    "        return 0\n"
)


def apply(root: Path) -> None:
    source = root / "pmb/chroot/apk_static.py"
    text = source.read_text()
    if text.count(OLD) != 1:
        raise ValueError("Expected pmbootstrap 1.50.1 version check was not found once")
    progress_source = root / "pmb/helpers/apk.py"
    progress = progress_source.read_text()
    if progress.count(OLD_PROGRESS) != 1:
        raise ValueError("Expected pmbootstrap 1.50.1 progress parser was not found once")
    source.write_text(text.replace(OLD, NEW, 1))
    progress_source.write_text(progress.replace(OLD_PROGRESS, NEW_PROGRESS, 1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pmbootstrap", type=Path)
    apply(parser.parse_args().pmbootstrap)
