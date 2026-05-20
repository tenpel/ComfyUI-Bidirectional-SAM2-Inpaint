# Bidirectional Tracking Patch for ComfyUI-segment-anything-2

## 🛑 What is this?
This is a patched version of `nodes.py` for [kijai/ComfyUI-segment-anything-2](https://github.com/kijai/ComfyUI-segment-anything-2). 

## ❓ Why is it needed?
The original SAM2 implementation in ComfyUI was hardcoded to track forward starting from `frame_index = 0`. 
When doing advanced video inpainting (especially for long videos split into chunks), we often use detection models (like Qwen-VL or Florence2) that detect the target object on a specific keyframe in the middle of a chunk. 

If the target is detected on Frame 72, the original SAM2 node could not track it backwards to Frame 0.
We modified the code to:
1. Allow `frame_index` to be an input for `Sam2VideoSegmentationAddPoints`.
2. Automatically run `propagate_in_video` in **both directions** (forward and reverse) from the starting `frame_index`, ensuring the mask covers the entire video sequence perfectly.

## 🛠️ How to install
1. Make sure you have installed the original [ComfyUI-segment-anything-2](https://github.com/kijai/ComfyUI-segment-anything-2) via ComfyUI Manager.
2. Navigate to your ComfyUI directory: `ComfyUI/custom_nodes/ComfyUI-segment-anything-2/`
3. Back up the original `nodes.py` (e.g. rename it to `nodes_backup.py`).
4. Copy the `nodes.py` from this folder and overwrite the one in the `ComfyUI-segment-anything-2` folder.
5. Restart ComfyUI. 

You will now see the updated nodes with bidirectional tracking support!

## 📜 License
This modified file originates from the Kijai `ComfyUI-segment-anything-2` repository and is subject to the **Apache License 2.0**.
As required by the license:
- A copy of the Apache 2.0 license is included in this directory (`LICENSE`).
- We explicitly state that `nodes.py` was modified from the original to add the `frame_index` argument and bidirectional propagation logic.
