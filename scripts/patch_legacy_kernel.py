#!/usr/bin/env python3
"""Add a binutils compatibility patch to the pinned dory kernel aport."""

import argparse
import hashlib
from pathlib import Path


PATCH_NAME = "binutils-modern-arm-section-flags.patch"
PATCH = """--- a/arch/arm/mm/proc-v7.S
+++ b/arch/arm/mm/proc-v7.S
@@ -417,7 +417,7 @@
 \tstring\tcpu_elf_name, "v7"
 \t.align
 
-\t.section ".proc.info.init", #alloc, #execinstr
+\t.section ".proc.info.init", "ax", %progbits
 
 \t/*
 \t * Standard v7 proc info content
--- a/arch/arm/boot/compressed/head.S
+++ b/arch/arm/boot/compressed/head.S
@@ -114,7 +114,7 @@
 #endif
 \t\t.endm
\x20
-\t\t.section ".start", #alloc, #execinstr
+\t\t.section ".start", "ax", %progbits
 /*
  * sort out different calling conventions
  */
--- a/arch/arm/boot/compressed/piggy.gzip.S
+++ b/arch/arm/boot/compressed/piggy.gzip.S
@@ -1,4 +1,4 @@
-\t.section .piggydata,#alloc
+\t.section .piggydata,"a",%progbits
 \t.globl\tinput_data
 input_data:
 \t.incbin\t"arch/arm/boot/compressed/piggy.gzip"
"""


def patch(root: Path) -> None:
    directory = root / "device/testing/linux-lg-dory"
    apkbuild = directory / "APKBUILD"
    source = apkbuild.read_text()
    source_marker = "\tgcc10-extern_YYLOC_global_declaration.patch\n"
    sum_marker = "  gcc10-extern_YYLOC_global_declaration.patch\""
    if source.count(source_marker) != 1 or source.count(sum_marker) != 1:
        raise ValueError("Unexpected pinned linux-lg-dory APKBUILD layout")
    digest = hashlib.sha512(PATCH.encode()).hexdigest()
    updated = source.replace(source_marker, source_marker + f"\t{PATCH_NAME}\n", 1)
    updated = updated.replace(
        sum_marker,
        "  gcc10-extern_YYLOC_global_declaration.patch\n"
        f"{digest}  {PATCH_NAME}\"",
        1,
    )
    (directory / PATCH_NAME).write_text(PATCH)
    apkbuild.write_text(updated)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pmaports", type=Path)
    args = parser.parse_args()
    patch(args.pmaports)
