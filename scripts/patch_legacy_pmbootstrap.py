#!/usr/bin/env python3
"""Allow apk.static to report an exact package revision in pmbootstrap 1.50.1.

The signed binary and APKINDEX package version must still match. Older apk
versions reported only the upstream version, while apk 3 also reports -rN.
"""

import argparse
from pathlib import Path


OLD = 'if not version.startswith(f"{version_bin}-r"):'
NEW = 'if version_bin != version and not version.startswith(f"{version_bin}-r"):'


def apply(root: Path) -> None:
    source = root / "pmb/chroot/apk_static.py"
    text = source.read_text()
    if text.count(OLD) != 1:
        raise ValueError("Expected pmbootstrap 1.50.1 version check was not found once")
    source.write_text(text.replace(OLD, NEW, 1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pmbootstrap", type=Path)
    apply(parser.parse_args().pmbootstrap)
