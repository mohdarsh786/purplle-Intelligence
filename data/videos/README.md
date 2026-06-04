# CCTV Video Feeds Directory

> [!NOTE]
> This directory originally stored all CCTV video files. To support multiple store locations, these video assets are now organized on a store-by-store basis under:
> `data/stores/store_<id>/videos/`

## 📂 Required Files & Placement

Raw CCTV video streams should now be placed under the respective store folders:
* **Store 1 Videos**: `data/stores/store_1/videos/cam1_zone.mp4`, `cam2_zone.mp4`, etc.
* **Store 2 Videos**: `data/stores/store_2/videos/entry_1.mp4`, `entry_2.mp4`, etc.

## ⚠️ Git Commit Exclusions

As per the Purplle Tech Challenge 2026 rules:
* Heavy video assets (CCTV footage) are strictly **excluded from being committed to GitHub**.
* The root `.gitignore` ignores all video extensions (`.mp4`, `.avi`, `.mov`) across all stores under the `data/stores/` structure.
* Only the directory structure, the `.gitkeep` placeholder, and this documentation file should reside in the remote repository.
