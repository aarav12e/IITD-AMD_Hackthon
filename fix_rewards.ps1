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
        if ($cell.source -is [Array]) {
            $sourceStr = -join $cell.source
        } else {
            $sourceStr = $cell.source
        }

        # Fix Reward Function logic (Cell ID: 351689ea)
        if ($sourceStr -like "*def gameplay_scores*") {
            Write-Host "Fixing gameplay_scores function logic..."
            
            # We will construct the CORRECT source code for this cell
            # Replacing 'game.board' with 'game._board'
            # Replacing '== "M"' with '== -1'
            
            $newSource = @(
                "import numpy as np`n",
                "import json`n",
                "`n",
                "def valid_json_reward(completions, **kwargs):`n",
                "    scores = []`n",
                "    for completion in completions:`n",
                "        try:`n",
                "            response = completion[0][`"content`"]`n",
                "            action = parse_llm_action(response)`n",
                "            # Strong positive reward for valid JSON`n",
                "            if action is not None:`n",
                "                scores.append(1.0)  # Reduced from 10.0 to balance gradients`n",
                "            else:`n",
                "                scores.append(-1.0)`n",
                "        except Exception as e:`n",
                "            scores.append(0.0)`n",
                "    return scores`n",
                "`n",
                "`n",
                "def gameplay_scores(completions, **kwargs):`n",
                "    scores = []`n",
                "    seeds = kwargs.get(`"seed`", [])`n",
                "    move_histories = kwargs.get(`"move_history`", [])`n",
                "`n",
                "    for idx, completion in enumerate(completions):`n",
                "        try:`n",
                "            response = completion[0][`"content`"]`n",
                "            action = parse_llm_action(response)`n",
                "`n",
                "            # If JSON invalid, give small penalty only`n",
                "            if action is None:`n",
                "                scores.append(-0.5)`n",
                "                continue`n",
                "`n",
                "            # If JSON valid but no game context`n",
                "            if idx >= len(seeds) or idx >= len(move_histories):`n",
                "                scores.append(0.0)`n",
                "                continue`n",
                "`n",
                "            seed = seeds[idx]`n",
                "            move_history_raw = move_histories[idx]`n",
                "`n",
                "            if isinstance(move_history_raw, str):`n",
                "                move_history = json.loads(move_history_raw)`n",
                "            else:`n",
                "                move_history = move_history_raw`n",
                "`n",
                "            game = MinesweeperGame(rows=6, cols=6, num_mines=5, seed=seed)`n",
                "`n",
                "            for prev_action in move_history:`n",
                "                game.do_action(prev_action)`n",
                "`n",
                "            row = action.get(`"row`")`n",
                "            col = action.get(`"col`")`n",
                "            action_type = action.get(`"type`")`n",
                "`n",
                "            if row is None or col is None or action_type is None:`n",
                "                scores.append(-0.5)`n",
                "                continue`n",
                "`n",
                "            if not (0 <= row < game.rows and 0 <= col < game.cols):`n",
                "                scores.append(-1.0)`n",
                "                continue`n",
                "`n",
                "            visible_board = game.get_visible_board()`n",
                "`n",
                "            # If revealing already revealed cell`n",
                "            if visible_board[row][col] != `".`":`n",
                "                scores.append(-0.5)`n",
                "                continue`n",
                "`n",
                "            # Reveal logic`n",
                "            if action_type == `"reveal`":`n",
                "                result = game.do_action(action)`n",
                "                if result == `"mine`":`n",
                "                    scores.append(-2.0)`n",
                "                else:`n",
                "                    # Reward based on information gain (simplified)`n",
                "                    scores.append(1.0)`n",
                "`n",
                "            # Flag logic`n",
                "            elif action_type == `"flag`":`n",
                "                # FIXED: Access _board (private) and check for -1 (mine)`n",
                "                if game._board[row][col] == -1:`n",
                "                    scores.append(2.0)`n",
                "                else:`n",
                "                    scores.append(-1.0)`n",
                "`n",
                "            else:`n",
                "                scores.append(-0.5)`n",
                "        except Exception as e:`n",
                "            print(f`"Error in reward calc: {e}`")`n",
                "            scores.append(0.0)`n",
                "`n",
                "    return scores"
            )
            $cell.source = $newSource
        }
    }
}

# Write back to file with specific depth
$jsonOutput = $jsonContent | ConvertTo-Json -Depth 100
Set-Content -Path $notebookPath -Value $jsonOutput -Encoding UTF8

Write-Host "Notebook rewards fixed successfully!"
