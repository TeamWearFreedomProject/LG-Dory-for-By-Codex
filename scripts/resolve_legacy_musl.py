#!/usr/bin/env python3
"""Use signed Alpine stable musl APKs in a disposable 2022 pmaports clone.

The old edge APKs have disappeared. A stable APK of the same version is a
different artifact, so record its digest only after apk.static verifies its
signature and contents with trusted Alpine keys.
"""

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
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


def package_url(branch: str, package: str) -> str:
    return f"{MIRROR}/{branch}/main/armhf/{package}-{VERSION}.apk"


def available(branch: str, package: str) -> bool:
    request = urllib.request.Request(package_url(branch, package), method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status == 200
    except (urllib.error.HTTPError, urllib.error.URLError) as error:
        print(f"Unavailable: {package_url(branch, package)} ({error})")
        return False


def update_checksum(source: str, alias: str, digest: str) -> str:
    pattern = rf"(?m)^[0-9a-f]{{128}}(  {re.escape(alias)})$"
    updated, count = re.subn(pattern, lambda match: digest + match.group(1), source)
    if count != 1:
        raise ValueError(f"Expected exactly one checksum for {alias}")
    return updated


def resolve(root: Path, apk_static: Path, keys_dir: Path, distfiles: Path) -> str:
    path = root / "cross/musl-armhf/APKBUILD"
    source = path.read_text()
    if source.count(OLD_MIRROR) != 1 or source.count(OLD_PATH) != 2:
        raise ValueError("Unexpected pinned musl-armhf source layout")
    if "pkgver=1.2.3\npkgrel=4\n" not in source:
        raise ValueError("Unexpected pinned musl-armhf package version")
    if not apk_static.is_file():
        raise ValueError("APK_STATIC_MISSING")
    if not os.access(apk_static, os.X_OK):
        raise ValueError("APK_STATIC_NOT_EXECUTABLE")
    if not list(keys_dir.glob("*.pub")):
        raise ValueError("ALPINE_KEYS_MISSING")

    for branch in BRANCHES:
        if not all(available(branch, package) for package in PACKAGES):
            continue
        with tempfile.TemporaryDirectory() as temporary:
            paths = {}
            for package in PACKAGES:
                alias = f"{package}-{VERSION}-armhf-edge.apk"
                target = Path(temporary) / alias
                with urllib.request.urlopen(package_url(branch, package), timeout=60) as response:
                    with target.open("wb") as output:
                        shutil.copyfileobj(response, output)
                paths[alias] = target

            # apk verify checks package signature and contents. Do not alter
            # expected digests or reuse downloads if this command fails.
            result = subprocess.run(
                [str(apk_static), "--keys-dir", str(keys_dir), "verify",
                 *(str(p) for p in paths.values())],
                capture_output=True, text=True,
            )
            if result.returncode:
                output = (result.stdout + result.stderr).lower()
                if "untrusted signature" in output or "untrusted" in output:
                    raise RuntimeError("APK_SIGNATURE_UNTRUSTED")
                if "unknown option" in output or "unknown command" in output:
                    raise RuntimeError("APK_VERIFY_COMMAND_UNSUPPORTED")
                raise RuntimeError("APK_VERIFY_FAILED")
            updated = source.replace(OLD_MIRROR, NEW_MIRROR, 1)
            updated = updated.replace(OLD_PATH, f"::$_mirror/{branch}/main/$_arch/")
            for alias, target in paths.items():
                digest = hashlib.sha512(target.read_bytes()).hexdigest()
                updated = update_checksum(updated, alias, digest)

            distfiles.mkdir(parents=True, exist_ok=True)
            for alias, target in paths.items():
                shutil.copy2(target, distfiles / alias)
            path.write_text(updated)
            print(f"Verified signed Alpine {branch} musl ARMHF APKs; recorded SHA-512")
            return branch
    raise RuntimeError("The pinned musl and musl-dev ARMHF APKs were not found")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pmaports", type=Path)
    parser.add_argument("--apk-static", type=Path, required=True)
    parser.add_argument("--keys-dir", type=Path, required=True)
    parser.add_argument("--distfiles", type=Path, required=True)
    args = parser.parse_args()
    try:
        resolve(args.pmaports, args.apk_static, args.keys_dir, args.distfiles)
    except (ValueError, RuntimeError, urllib.error.URLError) as error:
        code = str(error) if isinstance(error, (ValueError, RuntimeError)) else "DOWNLOAD_FAILED"
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::error title=Legacy musl preparation::{code}", flush=True)
        raise
