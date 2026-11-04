#!/usr/bin/env python3
"""Allow the pinned GCC 6 cross compiler to build with modern abuild flags."""

import argparse
from pathlib import Path


def patch(root: Path) -> None:
    path = root / "cross/gcc6-armhf/APKBUILD"
    original = path.read_text()
    marker = 'export CXXFLAGS="$CPPFLAGS $CXXFLAGS"'
    if original.count(marker) != 2:
        raise ValueError("Unexpected pinned gcc6-armhf APKBUILD layout")
    # Modern Alpine enables -Werror=format-security. GCC 6's libcpp/expr.c
    # passes a variable warning message as a format string, so preserve the
    # warning but do not fail the build for this legacy compiler package.
    updated = original.replace(
        marker,
        marker + '\n\texport CXXFLAGS="$CXXFLAGS -Wno-error=format-security"',
    )
    path.write_text(updated)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pmaports", type=Path)
    args = parser.parse_args()
    patch(args.pmaports)
