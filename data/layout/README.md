# Store Layout Directory

> [!NOTE]
> This directory was originally designed to hold physical spatial floor layout grids and coordinates. To support multiple store locations, these layout assets are now organized on a store-by-store basis under:
> `data/stores/store_<id>/layout/`

## 📂 Required Files

Floor layout assets and floor plans are now located within their specific store folders:
* **Store 1 Layout**: `data/stores/store_1/layout/store_1_layout.png` and `data/stores/store_1/layout/Brigade Road - Store layoutc5f5d56.xlsx`
* **Store 2 Layout**: `data/stores/store_2/layout/store_2_layout.png`

## ⚠️ Git Commit Exclusions

As per the Purplle Tech Challenge 2026 rules:
* Store layout sheets (`.xlsx` / `.png`) are strictly **excluded from being committed to GitHub**.
* The root `.gitignore` ignores all layout sheets across all stores under the `data/stores/` structure.
* Only the directory structure, the `.gitkeep` placeholder, and this documentation file should reside in the remote repository.
