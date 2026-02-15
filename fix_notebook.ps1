$notebookPath = "minesweeper_grpo.ipynb"

if (-not (Test-Path $notebookPath)) {
    Write-Host "Error: $notebookPath not found."
    exit 1
}

# Read file content (ensure UTF8)
$jsonContent = Get-Content -Path $notebookPath -Raw -Encoding UTF8 | ConvertFrom-Json

# Iterate through cells
foreach ($cell in $jsonContent.cells) {
    if ($cell.cell_type -eq "code") {
        # Check source is array or string
        if ($cell.source -is [Array]) {
            $sourceStr = -join $cell.source
        } else {
            $sourceStr = $cell.source
        }

        # Fix 1: HF_HUB_CACHE
        if ($sourceStr -like "*HF_HUB_CACHE*root/.cache*") {
            Write-Host "Fixing HF_HUB_CACHE..."
            $cell.source = @(
                "import os`n",
                "# Use local cache or default system cache for cross-platform support`n",
                "# os.environ[`"HF_HUB_CACHE`"] = `"./.cache/huggingface`""
            )
        }

        # Fix 2: Model Loading
        if ($sourceStr -like "*FastLanguageModel.from_pretrained*" -and $sourceStr -like "*unsloth/gpt-oss-20b-BF16*") {
            Write-Host "Fixing Model Loading..."
            $cell.source = @(
                "from unsloth import FastLanguageModel`n",
                "import torch`n",
                "import os`n",
                "`n",
                "max_seq_length = 1024  # Max context length`n",
                "lora_rank = 16         # LoRA rank`n",
                "`n",
                "# auto-detect model path`n",
                "model_name = `"unsloth/gpt-oss-20b-BF16`"`n",
                "if os.path.exists(`"models/gpt-oss-20b`"):`n",
                "    model_name = `"models/gpt-oss-20b`"`n",
                "`n",
                "print(f`"Loading model from: {model_name}`")`n",
                "`n",
                "# Try loading with explicit torch_dtype`n",
                "model, tokenizer = FastLanguageModel.from_pretrained(`n",
                "    model_name = model_name,`n",
                "    load_in_4bit = False,`n",
                "    max_seq_length = max_seq_length,`n",
                "    torch_dtype = torch.bfloat16,`n",
                ")`n",
                "`n",
                "# Force model to cuda explicitly`n",
                "print(f`"Model device: {model.device}`")`n",
                "print(`"Model loaded successfully!`")"
            )
        }
    }
}

# Write back to file with specific depth to avoid overly deep structure
$jsonOutput = $jsonContent | ConvertTo-Json -Depth 100
Set-Content -Path $notebookPath -Value $jsonOutput -Encoding UTF8

Write-Host "Notebook fixed successfully!"
