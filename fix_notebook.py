import json
import os

NOTEBOOK_PATH = "minesweeper_grpo.ipynb"

def fix_notebook():
    if not os.path.exists(NOTEBOOK_PATH):
        print(f"Error: {NOTEBOOK_PATH} not found.")
        return

    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb_ content = json.load(f)

    cells = nb_content.get("cells", [])
    modified_count = 0

    for cell in cells:
        # Fix 1: Remove hardcoded HF_HUB_CACHE path (Cell ID: 4a3496fa)
        # Note: Cell IDs might vary if user edited, so we check source content too
        source_str = "".join(cell.get("source", []))
        if "HF_HUB_CACHE" in source_str and "/root/.cache" in source_str:
            print("Fixing HF_HUB_CACHE path...")
            cell["source"] = [
                "import os\n",
                "# Use local cache or default system cache for cross-platform support\n",
                "# os.environ[\"HF_HUB_CACHE\"] = \"./.cache/huggingface\""
            ]
            modified_count += 1

        # Fix 2: Improve Model Loading (Cell ID: f3ac8394)
        if "FastLanguageModel.from_pretrained" in source_str and "gpt-oss-20b" in source_str:
            print("Fixing Model Loading path...")
            new_source = [
                "from unsloth import FastLanguageModel\n",
                "import torch\n",
                "import os\n",
                "\n",
                "max_seq_length = 1024  # Max context length\n",
                "lora_rank = 16         # LoRA rank\n",
                "\n",
                "# auto-detect model path\n",
                "model_name = \"unsloth/gpt-oss-20b-BF16\"\n",
                "if os.path.exists(\"models/gpt-oss-20b\"):\n",
                "    model_name = \"models/gpt-oss-20b\"\n",
                "\n",
                "print(f\"Loading model from: {model_name}\")\n",
                "\n",
                "# Try loading with explicit torch_dtype\n",
                "model, tokenizer = FastLanguageModel.from_pretrained(\n",
                "    model_name = model_name,\n",
                "    load_in_4bit = False,\n",
                "    max_seq_length = max_seq_length,\n",
                "    torch_dtype = torch.bfloat16,\n",
                ")\n",
                "\n",
                "# Force model to cuda explicitly\n",
                "print(f\"Model device: {model.device}\")\n",
                "print(\"Model loaded successfully!\")"
            ]
            cell["source"] = new_source
            modified_count += 1
            
        # Fix 3: Ensure format_state_for_llm matches perfectly with agent (Cell ID: e48cee13)
        # It seems mostly fine, but let's ensure the prompt template is exactly as desired.
        # Actually, the agent code was just updated to match this notebook, so they should be in sync now.
        # But let's check if the notebook uses `indent=2` in json.dumps
        if "format_state_for_llm" in source_str and "json.dumps" in source_str:
             if "indent=2" not in source_str:
                 print("Fixing json.dumps indent in format_state_for_llm...")
                 # (It was already present in the view_file output, so we might not need this edit, 
                 # but good to be safe if I missed it).
                 # Wait, looking at view_file, line 458: `{json.dumps(state, indent=2)}`
                 # So it is already correct.
                 pass

    # Save back
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(nb_content, f, indent=1)
        
    print(f"Notebook fixed! {modified_count} cells updated.")

if __name__ == "__main__":
    fix_notebook()
