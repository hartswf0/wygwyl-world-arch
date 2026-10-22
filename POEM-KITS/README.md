# POEM-KITS Archive Directory

This directory contains the original monolithic `.zip` archives of the WYGWYL production kits.

## ⚠️ Important Git & GitHub Notice:
Several of these `.zip` files exceed 100 MB (`Poem_07`: 114MB, `Poem_08`: 100MB, `Poem_13`: 134MB, `Poem_14`: 101MB, `Poet-GEMINI`: 146MB).
**Do NOT commit these raw `.zip` files directly to standard Git commits**, as GitHub's pre-receive hook will immediately reject the push with:
`remote: error: GH001: Large files detected. File exceeds GitHub's file size limit of 100.00 MB`

## How These Are Handled:

1. **Unpacked Working Assets (Tracked in Git)**:
   All 14 poem kits + the 31-piece modular Poet kit are unpacked and organized under:
   `shots/kits/packs/`
   Every individual PNG, SVG, and JSON inside is under 3.8 MB, allowing full Git versioning, immediate agent accessibility, and direct web rendering.
   See [shots/kits/packs/README.md](../shots/kits/packs/README.md).

2. **Monolithic Archive Distribution (GitHub Releases)**:
   To push or download the full pristine `.zip` archives, use GitHub Releases:
   ```bash
   # Create a release and upload the heavy zip bundles (up to 2GB per file):
   gh release create v2.0-poem-kits POEM-KITS/*.zip --title "WYGWYL Poem Kits v2.0 Monolithic Archives"

   # Download all zips on a remote machine:
   gh release download v2.0-poem-kits --dir POEM-KITS/
   ```

3. **Automated Slicing & Part Segmentation**:
   To cut any sheet apart into transparent cards with brass brad detection:
   ```bash
   python3 shots/kits/slice_kit_sheets.py <sheet_or_directory> <output_dir>
   ```
