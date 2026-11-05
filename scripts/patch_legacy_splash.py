#!/usr/bin/env python3
"""Work around the 2022 splash tar pipeline failing in ARMHF buildroot."""

import argparse
from pathlib import Path


UNPACK = '''unpack() {
	fetch || return 1
	python3 - "$srcdir" "$srcdir/postmarketos-splash-$pkgver.tar.gz" <<'PY'
import sys
import tarfile

with tarfile.open(sys.argv[2], "r:gz") as archive:
    archive.extractall(sys.argv[1], filter="data")
PY
}

'''


def patch(root: Path) -> None:
    path = root / "main/postmarketos-splash/APKBUILD"
    source = path.read_text()
    marker = "package() {\n"
    if source.count(marker) != 1 or "pkgver=1.0.0\n" not in source:
        raise ValueError("Unexpected pinned postmarketos-splash APKBUILD layout")
    if "unpack() {" in source:
        raise ValueError("Upstream splash already defines unpack")
    path.write_text(source.replace(marker, UNPACK + marker, 1))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pmaports", type=Path)
    args = parser.parse_args()
    patch(args.pmaports)
