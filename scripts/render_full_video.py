import json
import urllib.request
import urllib.parse
import time
import os
import subprocess
import cv2

# ================= BEÁLLÍTÁSOK =================
COMFY_API = "http://127.0.0.1:8188"

# FIGYELEM: A scriptet a ComfyUI főkönyvtárában (a python_embeded mellett) futtasd!
WORKFLOW_API_PATH = "workflow_api.json"  # A ComfyUI-ban elmentett API workflow json
INPUT_VIDEO = r"input\parking.mp4"       # A bemeneti videód relatív útvonala (ComfyUI/input/...)
OUTPUT_DIR = r"output"                   # A kimeneti mappa relatív útvonala (ComfyUI/output)
CHUNK_SIZE = 81                          # Egyben renderelendő képkockák száma (RTX 3080/16GB esetén 81 a stabil maximum Wan 1.3B fp16-nál)
# ===============================================

def get_video_frame_count(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Nem sikerült megnyitni a videót: {video_path}")
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return count

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"{COMFY_API}/prompt", data=data)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Hiba a küldés során: {e}")
        return None

def check_history(prompt_id):
    req = urllib.request.Request(f"{COMFY_API}/history/{prompt_id}")
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read())
            return prompt_id in res
    except:
        return False

def main():
    if not os.path.exists(WORKFLOW_API_PATH):
        print(f"HIBA: Nem található a {WORKFLOW_API_PATH} fájl!")
        print("Mentsd el a workflow-t 'Save (API)' gombbal a ComfyUI-ban, a script mellé!")
        return

    if not os.path.exists(INPUT_VIDEO):
        print(f"HIBA: Nem található a bemeneti videó: {INPUT_VIDEO}")
        return

    with open(WORKFLOW_API_PATH, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Keresd meg a LoadVideo és a VHS_VideoCombine node-okat
    load_video_id = None
    combine_id = None
    for node_id, node in workflow.items():
        if node.get("class_type") == "LoadVideo":
            load_video_id = node_id
        if node.get("class_type") == "VHS_VideoCombine" and "Save Mask" not in str(node.get("_meta", {}).get("title", "")):
            combine_id = node_id

    if not load_video_id or not combine_id:
        print("HIBA: Nem található a LoadVideo vagy a fő VHS_VideoCombine node a workflow-ban!")
        return

    total_frames = get_video_frame_count(INPUT_VIDEO)
    print(f"A videó teljes hossza: {total_frames} képkocka.")

    generated_chunks = []
    chunk_idx = 0

    for start_frame in range(0, total_frames, CHUNK_SIZE):
        print(f"\n--- {chunk_idx + 1}. darab generálása kezdődik ---")
        print(f"Képkockák: {start_frame} - {min(start_frame + CHUNK_SIZE, total_frames)}")

        # Módosítjuk a beállításokat a darabhoz
        workflow[load_video_id]["inputs"]["skip_first_frames"] = start_frame
        workflow[load_video_id]["inputs"]["frame_load_cap"] = CHUNK_SIZE
        
        chunk_prefix = f"wan_chunk_{chunk_idx:03d}"
        workflow[combine_id]["inputs"]["filename_prefix"] = chunk_prefix

        # Küldés a ComfyUI-nak
        res = queue_prompt(workflow)
        if not res:
            print("Kritikus hiba, leállás.")
            break
            
        prompt_id = res['prompt_id']
        print(f"Feladat elküldve! Prompt ID: {prompt_id}")
        print("Várakozás a befejezésre (ez több percig is eltarthat)...")

        # Polling (várjuk, amíg a history-ban megjelenik)
        while not check_history(prompt_id):
            time.sleep(5)
            
        print(f"-> {chunk_idx + 1}. darab KÉSZ!")
        generated_chunks.append(chunk_prefix)
        chunk_idx += 1

    print("\n=========================================")
    print("MINDEN DARAB LEGENERÁLVA!")
    print("Most összefűzzük a videót ffmpeg-gel...")

    actual_files = []
    for prefix in generated_chunks:
        matching_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(prefix) and f.endswith(".mp4")]
        if matching_files:
            matching_files.sort(key=lambda x: os.path.getmtime(os.path.join(OUTPUT_DIR, x)), reverse=True)
            actual_files.append(os.path.join(OUTPUT_DIR, matching_files[0]))

    if len(actual_files) == len(generated_chunks):
        list_file_path = os.path.join(OUTPUT_DIR, "concat_list.txt")
        with open(list_file_path, "w", encoding="utf-8") as lf:
            for f in actual_files:
                lf.write(f"file '{os.path.abspath(f)}'\n")
        
        final_output = os.path.join(OUTPUT_DIR, "FINAL_FULL_VIDEO.mp4")
        
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_path, 
            "-c", "copy", final_output
        ]
        
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"\nSiker! A végső videó elkészült: {final_output}")
    else:
        print("Hiba az összefűzésnél: nem találom az összes legenerált darabot az output mappában!")

if __name__ == "__main__":
    main()
