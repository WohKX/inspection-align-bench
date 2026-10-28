# Landmarks of the VisA parts

Hand-clicked with `tools/landmark_picker.html` (format: DATA_FORMAT.md, section 2). Licence: CC BY 4.0, made on VisA images
(Zou et al., ECCV 2022); credit: Kai Xuan.

| folder | VisA class | images |
|---|---|---|
| `pcb/` | `pcb1` | 3 goldens + 40 test images |
| `pcb_calib/` | `pcb1` | the same 3 goldens + 10 calibration images |
| `chewing_gum/` | `chewinggum` | 3 goldens + 40 test images |
| `chewing_gum_calib/` | `chewinggum` | the same 3 goldens + 10 calibration images |
| `fryum/` | `fryum` | 3 goldens + 40 test images |
| `fryum_calib/` | `fryum` | the same 3 goldens + 10 calibration images |

Each folder holds one `landmarks.json`; the file names of the images it needs are listed inside it. The MVTec AD parts (metal
nut, screw) are not published here, because that dataset's licence is non-commercial share-alike.
