#!/usr/bin/python3
"""
Minesweeper Model
Loads base GPT-OSS model from local HuggingFace snapshot.
"""

import time
import os
import torch
from pathlib import Path
from typing import Optional, List
from transformers import AutoModelForCausalLM, AutoTokenizer


class MinesweeperAgent(object):
    def __init__(self, **kwargs):

        # Search for model in priority order:
        # 1. Environment variable
        # 2. Local directory relative to this file
        # 3. Default HF Hub ID
        
        default_model_id = "unsloth/gpt-oss-20b-BF16"
        candidates = []
        
        # Check env var
        import os
        if "MINESWEEPER_MODEL_PATH" in os.environ:
            candidates.append(Path(os.environ["MINESWEEPER_MODEL_PATH"]))
            
        # Check local models directory
        local_models = Path(__file__).parent.parent / "models"
        if local_models.exists():
            # Look for subdirectories that might be the model
            for d in local_models.iterdir():
                if d.is_dir():
                    candidates.append(d)
                    
        # Check standard cache locations (optional, but good for offline if copied)
        # Windows: %USERPROFILE%/.cache/huggingface/hub/...
        
        model_name = default_model_id # Fallback
        
        for cand in candidates:
            if cand.exists():
                print(f"Found local model at: {cand}")
                model_name = str(cand)
                break
                
        print(f"Loading model from: {model_name}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            padding_side="left"
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )

        self.model.eval()

    def generate_response(
        self,
        message: str | List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> tuple:

        if system_prompt is None:
            system_prompt = (
                "You are an expert Minesweeper solver. "
                "Output ONLY valid JSON."
            )

        if isinstance(message, str):
            message = [message]

        texts = []
        for msg in message:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": msg},
            ]

            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )

            texts.append(text)

        model_inputs = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True
        ).to(self.model.device)

        tgps_show = kwargs.get("tgps_show", False)

        if tgps_show:
            start_time = time.time()

        with torch.no_grad():
            generated_ids = self.model.generate(
    **model_inputs,
    max_new_tokens=kwargs.get("max_new_tokens", 20),
    do_sample=True,
    temperature=kwargs.get("temperature", 0.8),
    pad_token_id=self.tokenizer.pad_token_id,
    eos_token_id=self.tokenizer.eos_token_id
)

        if tgps_show:
            generation_time = time.time() - start_time

        output_tokens = generated_ids[:, model_inputs.input_ids.shape[1]:]

        outputs = self.tokenizer.batch_decode(
            output_tokens,
            skip_special_tokens=True
        )

        outputs = [o.strip() for o in outputs]
        print("RAW MODEL OUTPUT:", outputs[0])

        if tgps_show:
            token_len = sum(len(output_tokens[i]) for i in range(len(output_tokens)))
            return outputs[0], token_len, generation_time

        return outputs[0], None, None


if __name__ == "__main__":
    agent = MinesweeperAgent()

    test_prompt = """
You are playing Minesweeper.

Game state:
{
  "board": [
    [".", ".", "."],
    [".", "1", "."],
    [".", ".", "."]
  ],
  "rows": 3,
  "cols": 3,
  "mines": 1
}

Output your next action as JSON:
"""

    response, tl, tm = agent.generate_response(
        test_prompt,
        tgps_show=True,
        max_new_tokens=128
    )

    print("Response:", response)

    if tl and tm:
        print(f"Tokens: {tl}, Time: {tm:.2f}s")