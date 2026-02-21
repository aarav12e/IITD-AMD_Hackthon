# 💣 MineRL-LLM — Reinforcement Learning Powered Minesweeper Agent

> 🏆 Developed during the AMD AI Hackathon at IIT Delhi  
> 🔥 Fine-tuned GPT-OSS-20B using LoRA + GRPO on AMD GPUs (ROCm)

---

## 🚀 Overview

MineRL-LLM is a Reinforcement Learning-based Large Language Model trained to play Minesweeper.

The model:

- 📥 Takes a JSON board state as input  
- 📤 Outputs a structured JSON action (`reveal` or `flag`)  
- 🎯 Learns optimal gameplay through GRPO (Group Relative Policy Optimization)  
- ⚡ Trained using Unsloth framework for accelerated LoRA finetuning  

This project demonstrates how LLMs can be adapted to structured decision-making environments using RL.

---

## 🧠 Training Approach

| Component | Details |
|------------|----------|
| Base Model | GPT-OSS-20B (BF16) |
| Finetuning | LoRA (Rank 16) |
| RL Method | GRPO |
| Framework | Unsloth |
| Hardware | AMD GPU (ROCm) |
| Dataset | 1000 dynamically generated Minesweeper states |

---

## 🏗 Model Architecture

- Low-Rank Adaptation (LoRA) applied to:
  - `q_proj`
  - `k_proj`
  - `v_proj`
  - `o_proj`
  - `gate_proj`
  - `up_proj`
  - `down_proj`

- Only ~0.04% parameters trained (~8M parameters)
- Base model weights remain frozen

---

## 🎮 Game Interface

### Input Format

```json
{
  "board": [[".", ".", "."], ["1", ".", "."], ["0", "1", "."]],
  "rows": 3,
  "cols": 3,
  "mines": 1,
  "flags_placed": 0,
  "cells_revealed": 2
}
