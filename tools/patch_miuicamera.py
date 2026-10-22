#!/usr/bin/env python3
"""Build a MiuiCamera APK with a fixed classes4.dex.

The source APK is the unmodified Xiaomi prebuilt.  We only replace its
classes4.dex, which contains CvWatermarkUtil.  The replacement adds a null
check before the ArcSoft/Xiaomi custom capture result is dereferenced while
saving an ultra-wide photo.  Without the check the camera-saver thread throws
a NullPointerException and the JPEG is never finalized.

Signature files are stripped here; the Soong android_app_import module signs
the resulting APK with the platform certificate.
"""

import os
import shutil
import sys
import zipfile


TARGET_DEX = "classes4.dex"


def is_signature_file(name):
    if name == "META-INF/MANIFEST.MF":
        return True
    if name.startswith("META-INF/"):
        return name.upper().endswith((".SF", ".RSA", ".DSA", ".EC"))
    return False


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: patch_miuicamera.py <source.apk> <classes4.dex> <out.apk>")

    src_apk, replacement_dex, out_apk = sys.argv[1:4]

    with open(replacement_dex, "rb") as f:
        dex_data = f.read()
    if not dex_data.startswith(b"dex\n"):
        sys.exit("replacement is not a dex file: %s" % replacement_dex)

    out_dir = os.path.dirname(os.path.abspath(out_apk))
    os.makedirs(out_dir, exist_ok=True)

    replaced = 0
    with zipfile.ZipFile(src_apk, "r") as zin, zipfile.ZipFile(out_apk, "w", allowZip64=True) as zout:
        for info in zin.infolist():
            name = info.filename
            if is_signature_file(name):
                continue

            if name == TARGET_DEX:
                zout.writestr(info, dex_data, compress_type=info.compress_type)
                replaced += 1
                continue

            if info.is_dir():
                zout.writestr(info, b"")
                continue

            with zin.open(info, "r") as src, zout.open(info, "w") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)

    if replaced != 1:
        sys.exit("expected exactly one %s in %s, found %d" % (TARGET_DEX, src_apk, replaced))

    print("patched %s -> %s (%d dex replacement)" % (src_apk, out_apk, replaced))


if __name__ == "__main__":
    main()
