# Raw Assets Directory

This directory is designated for storing raw and intermediate pipeline outputs during video processing and intelligence compilation.

## 📂 Expected Contents

Future assets placed here during analysis loops include:
* **Processed Clips**: Snippets of tracked highlights, queue congestion clips, or specific anomaly-triggered footage.
* **Extracted Frames**: Raw JPG/PNG frame assets extracted for object detection testing or Re-ID alignment.
* **Intermediate Exports**: Unformatted telemetry logs.

## ⚠️ Git Commit Exclusions

As per the Purplle Tech Challenge 2026 rules:
* All raw outputs, video clips, and frame assets are strictly **excluded from being committed to GitHub**.
* The `.gitignore` file at the root of the project has been updated to ignore all generated files inside `data/raw/` while preserving the `.gitkeep` and this documentation.
