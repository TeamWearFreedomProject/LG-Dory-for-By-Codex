#!/usr/bin/env python3
"""Find the original musl ARMHF APKs in an official Alpine stable archive.

Only the source URL in a disposable pmaports checkout changes. The SHA-512
checksums from the pinned 2022 APKBUILD remain untouched and are checked by
abuild after download.
"""

import argparse
import urllib.error
import urllib.request
from pathlib import Path


MIRROR = "https://dl-cdn.alpinelinux.org/alpine"
BRANCHES = ("v3.17", "v3.16", "v3.18")
PACKAGES = ("musl", "musl-dev")
VERSION = "1.2.3-r4"
OLD_MIRROR = '_mirror="http://dl-4.alpinelinux.org/alpine/"'
NEW_MIRROR = f'_mirror="{MIRROR}"'
OLD_PATH = "::$_mirror/edge/main/$_arch/"


def available(branch: str, package: str) -> bool:
    url = f"{MIRROR}/{branch}/main/armhf/{package}-{VERSION}.apk"
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status == 200
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        print(f"Unavailable: {url} ({error})")
        return False


def resolve(root: Path) -> str:
    path = root / "cross/musl-armhf/APKBUILD"
    source = path.read_text()
    if source.count(OLD_MIRROR) != 1 or source.count(OLD_PATH) != 2:
        raise ValueError("Unexpected pinned musl-armhf source layout")
    if "pkgver=1.2.3\npkgrel=4\n" not in source:
        raise ValueError("Unexpected pinned musl-armhf package version")
    for branch in BRANCHES:
        if all(available(branch, package) for package in PACKAGES):
            updated = source.replace(OLD_MIRROR, NEW_MIRROR, 1)
            updated = updated.replace(OLD_PATH, f"::$_mirror/{branch}/main/$_arch/")
            path.write_text(updated)
            print(f"Using official Alpine {branch} musl ARMHF APKs; SHA-512 unchanged")
            return branch
    raise RuntimeError("The pinned musl and musl-dev ARMHF APKs were not found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pmaports", type=Path)
    resolve(parser.parse_args().pmaports)
