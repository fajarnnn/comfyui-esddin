import json
import argparse
import sys

def generate_comfy_json(n_value, subject_name, output_filename):
    # Struktur Workflow ComfyUI (Template)
    workflow_template = {
        "36": {"inputs": {"directory_path": ["58", 0], "file_extension": "ALL", "reset_index": False, "sort_method": "numerical", "reload_directory": False, "read_caption": False, "starting_index": 0}, "class_type": "WWAA_ImageLoader", "_meta": {"title": "🪠️ WWAA Image Batch Loader"}},
        "46": {"inputs": {"delimiter": "_", "mode": "first_n", "n": str(n_value), "start": 1, "end": str(n_value), "join_delim": "", "line_delim": "\n", "strings": ["36", 3]}, "class_type": "CutFieldsToString", "_meta": {"title": "CutFieldsToString"}},
        "58": {"inputs": {"value": f"/workspace/runpod-slim/ComfyUI/input/qwen/{subject_name}"}, "class_type": "easy string", "_meta": {"title": "srcdir"}},
        "60": {"inputs": {"value": f"/workspace/runpod-slim/ComfyUI/input/qwen/{subject_name}/dupe"}, "class_type": "easy string", "_meta": {"title": "dupedir"}},
        "82": {"inputs": {"inputcount": 2, "Update inputs": None, "image_1": ["36", 0], "image_2": ["102:63", 0]}, "class_type": "ImageBatchMulti", "_meta": {"title": "Image Batch Multi"}},
        "101": {"inputs": {"preview": "", "previewMode": None, "source": ["102:102", 2]}, "class_type": "PreviewAny", "_meta": {"title": "Preview as Text"}},
        "105": {"inputs": {"init_score_ava": 0, "init_score_chad": 0, "init_score_ava2": 0, "init_score_other": 0, "init_score_avg": 0, "length": 0}, "class_type": "EmptyImageAndScores", "_meta": {"title": "EmptyImageAndScores"}},
        "111": {"inputs": {"batch": ["82", 0]}, "class_type": "BatchCount+", "_meta": {"title": "🔧 Batch Count"}},
        "134": {"inputs": {"prefix": "TOTALIMG:", "value": ["111", 0]}, "class_type": "ConsoleDebug+", "_meta": {"title": "🔧 Console Debug"}},
        "180": {"inputs": {"prefix": "main_name:", "value": ["46", 0]}, "class_type": "ConsoleDebug+", "_meta": {"title": "🔧 Console Debug"}},
        "182": {"inputs": {"prefix": "batchidx:", "value": ["36", 1]}, "class_type": "ConsoleDebug+", "_meta": {"title": "🔧 Console Debug"}},
        "224": {"inputs": {"string1": ["102:102", 2], "string2": ["36", 3]}, "class_type": "AppendStringsToList", "_meta": {"title": "Append Strings To List"}},
        "245": {"inputs": {"index": ["241:257", 8], "any": ["102:102", 2]}, "class_type": "easy indexAnything", "_meta": {"title": "Index Any"}},
        "246": {"inputs": {"prefix": "BESTIMAGE:", "value": ["245", 0]}, "class_type": "ConsoleDebug+", "_meta": {"title": "🔧 Console Debug"}},
        "247": {"inputs": {"prefix": "BEST_SCORE:", "value": ["241:257", 7]}, "class_type": "ConsoleDebug+", "_meta": {"title": "🔧 Console Debug"}},
        "248": {"inputs": {"filename_prefix": ["46", 0], "images": ["241:257", 6]}, "class_type": "SaveImage", "_meta": {"title": "Save Image"}},
        "254": {"inputs": {"any_1": ["224", 0], "any_2": ["241:257", 1], "any_3": ["241:257", 2], "any_4": ["241:257", 3], "any_5": ["241:257", 4], "any_6": ["241:257", 5]}, "class_type": "List of any [Crystools]", "_meta": {"title": "🪛 List of any"}},
        "255": {"inputs": {"prefix": "", "suffix": "", "input": ["254", 0]}, "class_type": "SomethingToString", "_meta": {"title": "Something To String"}},
        "256": {"inputs": {"root_dir": "input", "file": ["46", 0], "append": "overwrite", "insert": True, "text": ["255", 0]}, "class_type": "SaveText|pysssss", "_meta": {"title": "Save Text 🐍"}},
        "257": {"inputs": {"text": ["256", 0], "base_dir": "/workspace/runpod-slim/ComfyUI/input", "start_index": 0, "count": 12, "cols": 4, "thumb_size": 1024, "padding": 8, "recursive": True}, "class_type": "ScoreGridPreviewFromText", "_meta": {"title": "Score Grid Preview From Text"}},
        "258": {"inputs": {"images": ["257", 0]}, "class_type": "PreviewImage", "_meta": {"title": "Preview Image"}},
        "259": {"inputs": {"text_0": "files=2 | shown=2 | missing=0 | recursive=True | base_dir=/workspace/runpod-slim/ComfyUI/input", "text": ["257", 1]}, "class_type": "ShowText|pysssss", "_meta": {"title": "Show Text 🐍"}},
        "261": {"inputs": {"prefix": "BESTINDEX:", "value": ["241:257", 8]}, "class_type": "ConsoleDebug+", "_meta": {"title": "🔧 Console Debug"}},
        "262": {"inputs": {"images": ["241:257", 0]}, "class_type": "PreviewImage", "_meta": {"title": "Preview Image"}},
        "263": {"inputs": {"prefix": "All Image:", "value": ["36", 2]}, "class_type": "ConsoleDebug+", "_meta": {"title": "🔧 Console Debug"}},
        "102:49": {"inputs": {"string_a": ["46", 0], "string_b": "_*", "delimiter": ""}, "class_type": "StringConcatenate", "_meta": {"title": "Concatenate"}},
        "102:63": {"inputs": {"images": ["102:102", 0]}, "class_type": "ImageListToImageBatch", "_meta": {"title": "Image List to Image Batch"}},
        "102:47": {"inputs": {"dir_path": ["60", 0], "pattern": ["102:49", 0], "recursive": False, "return_full_path": True, "sort": True}, "class_type": "ListFilesFromDir", "_meta": {"title": "ListFilesFromDir"}},
        "102:102": {"inputs": {"paths": ["102:47", 0]}, "class_type": "LoadImagesFromStringList", "_meta": {"title": "LoadImagesFromStringList"}},
        "241:260": {"inputs": {"model_name": "sac+logos+ava1-l14-linearMSE.pth"}, "class_type": "LoadAesteticModel", "_meta": {"title": "LoadAesteticModel"}},
        "241:259": {"inputs": {"model_name": "chadscorer.pth"}, "class_type": "LoadAesteticModel", "_meta": {"title": "LoadAesteticModel"}},
        "241:258": {"inputs": {"model_name": "ava+logos-l14-linearMSE.pth"}, "class_type": "LoadAesteticModel", "_meta": {"title": "LoadAesteticModel"}},
        "241:257": {"inputs": {"use_v2_5": True, "min_types": 3, "image": ["82", 0], "aesthetic_model1": ["241:258", 0], "aesthetic_model2": ["241:259", 0], "aesthetic_model3": ["241:260", 0]}, "class_type": "CalculateAestheticScores3PlusV25", "_meta": {"title": "CalculateAestheticScores3PlusV25"}}
    }

    final_output = {"prompt": workflow_template}

    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2)
        print(f"✅ Berhasil! File '{output_filename}' dibuat.")
        print(f"   - Subject: {subject_name}")
        print(f"   - N Value: {n_value}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ComfyUI Workflow JSON")
    
    # Setup arguments
    parser.add_argument("--n", type=int, required=True, help="Nilai n")
    parser.add_argument("--subject", type=str, required=True, help="Nama subject")
    parser.add_argument("--filejson", type=str, required=True, help="Nama file output")

    args = parser.parse_args()

    # Eksekusi
    generate_comfy_json(args.n, args.subject, args.filejson)