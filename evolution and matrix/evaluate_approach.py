import sys
import json
import subprocess
import os

def calculate_iou(true_start, true_end, pred_start, pred_end):
    intersection_start = max(true_start, pred_start)
    intersection_end = min(true_end, pred_end)
    intersection = max(0, intersection_end - intersection_start)
    
    union_start = min(true_start, pred_start)
    union_end = max(true_end, pred_end)
    union = max(0, union_end - union_start)
    
    if union == 0:
        return 0.0
    return intersection / union

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run evaluate_approach.py <path_to_approach_script>")
        print("Example: uv run evaluate_approach.py ../diff-Approach/gemini-pipeline/approach.py")
        sys.exit(1)
        
    script_path = sys.argv[1]
    
    # Derive the name of the approach based on the folder it is in
    abs_script_path = os.path.abspath(script_path)
    parent_dir = os.path.dirname(abs_script_path)
    script_name = os.path.basename(parent_dir)
    
    # If the parent dir is diff-Approach itself, or something weird, handle it
    if script_name == "diff-Approach" or script_name == "Final-approach":
        pass # It's fine
        
    # Load ground truth
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gt_path = os.path.join(base_dir, "ground_truth.json")
    
    if not os.path.exists(gt_path):
        print(f"Error: Could not find {gt_path}")
        sys.exit(1)
        
    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)
        
    print(f"Running '{script_path}'...")
    print("Please wait. This may take several minutes depending on API calls and audio length.\\n")
    
    # Run the target script and capture output
    result = subprocess.run(
        ["uv", "run", script_path], 
        capture_output=True, 
        text=True,
        cwd=os.path.dirname(base_dir) # Run from project root so audio paths resolve correctly
    )
    
    # We will still try to parse standard output even if it crashed at the end
    output = result.stdout
    
    if result.returncode != 0:
        print(f"Warning: The script executed with an error (Code {result.returncode}). Evaluating any successful chunks...")
        print("Standard Error Output:\\n", result.stderr)

    marker = "EVALUATION OUTPUT (JSON FORMAT)"
    if marker not in output:
        print("Error: Could not find the EVALUATION OUTPUT JSON block in the script's output.")
        print("Raw Script Output:\\n")
        print(output)
        sys.exit(1)
        
    # Extract the JSON block at the bottom
    json_str = output.split(marker)[1]
    
    # Clean it up: split by the '========' boundary and take the payload
    if "=" * 52 in json_str:
        json_str = json_str.split("=" * 52)[-1]
    
    json_str = json_str.strip()
    
    try:
        predictions = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON output: {e}")
        print("String attempted to parse:\\n", json_str)
        sys.exit(1)
        
    metrics = {
        "approach_name": script_name,
        "files_evaluated": 0,
        "overall_mean_iou": 0.0,
        "overall_start_error_sec": 0.0,
        "overall_end_error_sec": 0.0,
        "details": {}
    }
    
    total_iou = 0.0
    total_start_err = 0.0
    total_end_err = 0.0
    conv_count = 0
    
    for audio_file, gt_convs in ground_truth.items():
        if audio_file not in predictions:
            metrics["details"][audio_file] = {"status": "Missing completely in predictions"}
            continue
            
        pred_convs = predictions[audio_file]
        file_metrics = {}
        
        for conv_m, gt_times in gt_convs.items():
            if conv_m not in pred_convs:
                file_metrics[conv_m] = {"status": "Missing or dropped"}
                continue
                
            p_times = pred_convs[conv_m]
            
            # Use safe gets in case the prediction dict is malformed internally
            p_start = p_times.get("start", 0.0)
            p_end = p_times.get("end", 0.0)
            
            g_start = gt_times.get("start", 0.0)
            g_end = gt_times.get("end", 0.0)
            
            iou = calculate_iou(g_start, g_end, p_start, p_end)
            s_err = abs(g_start - p_start)
            e_err = abs(g_end - p_end)
            
            file_metrics[conv_m] = {
                "IoU": round(iou, 4),
                "Start_Error_sec": round(s_err, 2),
                "End_Error_sec": round(e_err, 2),
                "pred_start": p_start,
                "pred_end": p_end,
                "true_start": g_start,
                "true_end": g_end
            }
            
            total_iou += iou
            total_start_err += s_err
            total_end_err += e_err
            conv_count += 1
            
        metrics["details"][audio_file] = file_metrics
        metrics["files_evaluated"] += 1
        
    if conv_count > 0:
        metrics["overall_mean_iou"] = round(total_iou / conv_count, 4)
        metrics["overall_start_error_sec"] = round(total_start_err / conv_count, 2)
        metrics["overall_end_error_sec"] = round(total_end_err / conv_count, 2)
        
    print("\\n" + "="*60)
    print(f"EVALUATION METRICS FOR: {script_name}")
    print("="*60)
    print(json.dumps(metrics, indent=2))
    
    # Save to JSON in the current directory (evolution and matrix)
    out_file = os.path.join(base_dir, f"{script_name}_metrics.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        
    print(f"\\n✅ Saved detailed metrics to: {out_file}")

if __name__ == "__main__":
    main()
