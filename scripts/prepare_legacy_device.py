#!/usr/bin/env python3
"""Apply a USB product ID to a disposable 2022 pmaports checkout."""

import argparse
import hashlib
import re
from pathlib import Path


def prepare(root: Path, product_id: str) -> None:
    if product_id not in {"0xD001", "0x4EE3"}:
        raise ValueError("USB product ID must be 0xD001 or 0x4EE3")
    device = root / "device/testing/device-lg-dory"
    info_path = device / "deviceinfo"
    apk_path = device / "APKBUILD"
    original = info_path.read_text()
    if original.count('deviceinfo_flash_method="fastboot"') != 1:
        raise ValueError("Unexpected 2022 deviceinfo layout")
    if "deviceinfo_usb_idProduct=" in original:
        raise ValueError("Upstream already sets USB product ID")
    updated = original.replace(
        'deviceinfo_flash_method="fastboot"',
        'deviceinfo_flash_method="fastboot"\n'
        'deviceinfo_usb_idProduct="' + product_id + '"',
        1,
    )
    apk = apk_path.read_text()
    checksum = hashlib.sha512(updated.encode()).hexdigest()
    apk, count = re.subn(
        r"[0-9a-f]{128}(  deviceinfo\s*)",
        lambda match: checksum + match.group(1),
        apk,
    )
    if count != 1:
        raise ValueError("Expected one deviceinfo checksum in APKBUILD")
    info_path.write_text(updated)
    apk_path.write_text(apk)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pmaports", type=Path)
    parser.add_argument("--product-id", choices=["0xD001", "0x4EE3"], required=True)
    args = parser.parse_args()
    prepare(args.pmaports, args.product_id)
