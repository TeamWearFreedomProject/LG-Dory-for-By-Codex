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
    dependency = " isl-dev "
    graphite = "\t\t--enable-cloog-backend \\\n"
    if original.count(dependency) != 1 or original.count(graphite) != 1:
        raise ValueError("Unexpected pinned GCC 6 graphite configuration")
    if original.count('options="!strip"') != 2 or original.count('depends="binutils-armhf mpc1"') != 1:
        raise ValueError("Unexpected pinned GCC 6 package dependencies")
    # Modern Alpine enables -Werror=format-security. GCC 6's libcpp/expr.c
    # passes a variable warning message as a format string, so preserve the
    # warning but do not fail the build for this legacy compiler package.
    updated = original.replace(
        marker,
        marker + '\n\texport CXXFLAGS="$CXXFLAGS -Wno-error=format-security"',
    )
    # The current isl-dev is 0.26, whose API no longer matches GCC 6's
    # Graphite code. Graphite is an optional loop optimization for GCC.
    updated = updated.replace(dependency, " ", 1)
    updated = updated.replace(graphite, "\t\t--without-isl \\\n", 1)
    # abuild 3.18 attempts to resolve the ARMHF ELF interpreter of target
    # files inside this x86_64 cross-compiler package. Keep explicit host
    # runtime dependencies instead of tracing those target ELF files.
    updated = updated.replace('options="!strip"', 'options="!strip !tracedeps"')
    updated = updated.replace('depends="binutils-armhf mpc1"',
                              'depends="binutils-armhf mpc1 libstdc++"', 1)
    path.write_text(updated)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pmaports", type=Path)
    args = parser.parse_args()
    patch(args.pmaports)
