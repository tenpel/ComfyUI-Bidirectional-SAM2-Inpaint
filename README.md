# ComfyUI Bidirectional SAM2 Inpaint Pipeline

This repository contains an automated, high-quality video inpainting pipeline for ComfyUI. It is specifically designed to handle long video sequences under strict VRAM limitations (e.g., 16GB RTX 3080 Laptops) by utilizing a chunking script, dynamic Qwen-VL detection, and a custom patched bidirectional SAM2 tracker combined with Wan 2.1 VACE.

## 🚀 Key Features

*   **Dynamic Subject Detection:** Uses `Qwen2.5-VL` to automatically detect specific textual targets (e.g. "the head and neck area of the female driver") rather than relying on static coordinates.
*   **Bidirectional SAM2 Tracking:** Includes a patched `nodes.py` for `ComfyUI-segment-anything-2`. Unlike the official node, this patch allows dynamic `frame_index` injection and runs video propagation both forwards and backwards, ensuring your mask is consistent throughout the entire chunk.
*   **VRAM Optimized Chunking:** Because full video generation models like Wan 2.1 will cause Out-Of-Memory (OOM) errors on standard GPUs for anything longer than ~80 frames, this repository includes an automated Python script (`render_full_video.py`). It feeds the video to ComfyUI in optimal 81-frame chunks and automatically concatenates them using `ffmpeg` when finished.
*   **Mask Expansion & Blur:** Integrates mask growing nodes to ensure smooth blending of inpainted subjects.

## 📦 What's Included

*   `workflows/video_wan_vace_inpainting.json` - The complete ComfyUI workflow.
*   `scripts/render_full_video.py` - The automated chunking and ffmpeg concatenation script.
*   `custom_nodes_patch/ComfyUI-segment-anything-2/` - The patched Python file to enable bidirectional SAM2 tracking.

## ⚙️ Prerequisites

You must have the following Custom Nodes installed via the ComfyUI Manager:
- `ComfyUI-VideoHelperSuite` (VHS)
- `Comfyui_Object_Detect_QWen_VL`
- `ComfyUI-segment-anything-2` (by Kijai)
- Models: Wan 2.1 (VAE, UNET, CLIP), Qwen2.5-VL-3B, SAM2.1 Hiera Base Plus.

## 🛠️ Installation & Setup

1. **Apply the SAM2 Patch:** 
   Navigate to the `custom_nodes_patch/ComfyUI-segment-anything-2/` folder in this repo, read the `PATCH_README.md`, and replace your existing SAM2 `nodes.py` with our patched version. Restart ComfyUI.
2. **Load the Workflow:**
   Drag and drop `video_wan_vace_inpainting.json` into your ComfyUI interface.
3. **Configure Inputs:**
   - Set your input video in the `LoadVideo` node.
   - Set your reference image (Note: for best results with Wan 2.1 VACE, use a tightly cropped RGB JPG image with a neutral background, not a transparent PNG).
   - Set your `QwenVLDetection` target (e.g. "the face").

## 🎥 Running the Automated Slicer Script

If your video is longer than ~81 frames (3.3 seconds at 24fps), do **not** run the workflow manually in the UI, as it will crash your GPU. Instead:

1. In ComfyUI, go to Settings (Gear icon) -> "Enable Dev mode Options".
2. Click the **"Save (API)"** button to export your configured workflow.
3. Save it as `workflow_api.json` in the same directory as the script.
4. Run the python script:
   ```bash
   python scripts/render_full_video.py
   ```
5. Grab a coffee. The script will automatically slice your video, queue the API prompts, wait for completion, and stich them together with `ffmpeg`.

## 💡 Practical Tips

*   **Reference frame per chunk:** For best identity/consistency results, don't reuse one global reference image. Export the keyframe you detect on, retouch it (apply your intended change to that still), and load it as the reference. When you continue with the next chunk (e.g. after the first 81 frames), repeat the process: grab a frame from the new chunk and retouch it again.
*   **Keep denoise lower than you'd expect:** Wan 2.1 VACE blends edits into the scene very aggressively. At high denoise values it integrates the change so well that it practically hides it. Lower the denoise until the edit stays clearly visible while still matching lighting and motion.
*   **Mask growth + blur:** A few pixels of mask expansion with feathered edges makes the seams disappear.

## ⚖️ Responsible Use

This pipeline can modify people's appearance in video. It is intended for creative and VFX work on footage you have the rights to use — costume/prop replacement, previsualization, restoration, and similar tasks. Do not use it to create misleading content or to depict real people without their consent. You are responsible for complying with the laws of your jurisdiction.

## 📜 License

This repository is licensed under the [MIT License](LICENSE). The patched `nodes.py` under `custom_nodes_patch/ComfyUI-segment-anything-2/` originates from [kijai/ComfyUI-segment-anything-2](https://github.com/kijai/ComfyUI-segment-anything-2) and remains under the Apache License 2.0 (see the LICENSE file in that folder).
