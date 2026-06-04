# Metadata Configurations Directory

This directory is designated for storing global application telemetry schemas, camera hardware parameters, and store business rules configurations.

## 📂 Contents & Descriptions

### 1. `camera_config.json`
* **Purpose**: Manages active camera settings, hardware parameters, spatial placement mappings, and frame processing properties.
* **Fields**: Tracks active camera streams (`active`, `video_source`), frame rates (`fps`), resolution definitions (`resolution`), and directional entry heuristics (`entry_direction`).

### 2. `store_config.json`
* **Purpose**: Manages global business rules, store operational hours, alert triggers, and bottleneck thresholds.
* **Fields**: Defines store opening/closing parameters (`store_open_time`, `store_close_time`), queue capacity metrics (`queue_threshold`), and store occupancy triggers (`crowd_threshold`).

---

## 💡 Engineering Rationale: Decoupling Configuration from Code

Decoupling store operational metadata and camera parameters from Python and React source code provides several key architectural advantages:

1. **Hot-Reloadable Attributes**: Operating thresholds (e.g. `queue_threshold`) and camera streams can be updated dynamically at runtime without requiring application recompilation, service restarts, or Docker image rebuilds.
2. **Environment Portability**: The same compiled application code can be deployed across multiple distinct retail branch locations simply by swapping the metadata configuration files.
3. **Decoupled Responsibilities**: Operations teams can tweak thresholds and add camera feeds without modifying or risk breaking backend analytical algorithms.

---

## 🛑 Assumptions

* **Verified Values**:
  * Camera files (`CAM 1.mp4` through `CAM 5.mp4`) are present and used as `video_source`.
  * Store location is Brigade Road, Bangalore based on layout (`Brigade Road - Store layoutc5f5d56.xlsx`) and POS (`Brigade_Bangalore_10_April_26 (1)bc6219c.csv`) filenames.
  * Zone names (`entry_zone`, `checkout_zone`, `exit_zone`) exist in `zones.json`.
* **Inferred Values**:
  * The cameras are currently set to `active: true`.
* **Unknown Values (TBD)**:
  * Exact physical `location` mapping of each camera to a zone.
  * Native video `fps` and `resolution` (requires CV2 analysis).
  * `entry_direction` mapping for each camera.
  * `store_open_time` and `store_close_time`.
  * Business operation values for `queue_threshold` and `crowd_threshold`.
