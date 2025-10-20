# LLM Code Generation Assignment

**Author:** Siyuan Cen  
**Email:** siyuanc4@andrew.cmu.edu  
**Date:** October 20, 2025  

---

## 🧩 Overview

This repository contains all code, prompts, and evaluation results for the **LLM Code Generation Assignment**. 
The project compares **GPT-4o (OpenAI)** and **Claude Sonnet 4.5 (Anthropic)** on Python code generation tasks, investigates failure cases, and introduces an improved prompting method called **Signature-Aware Prompting (SAP)**.

---

## ⚙️ Experimental Setup

### Models Tested
| Model             | Provider  | Access Method                                                |
| ----------------- | --------- | ------------------------------------------------------------ |
| GPT-4o            | OpenAI    | API (via `eval_gpt.py`)                                      |
| Claude Sonnet 4.5 | Anthropic | WebUI (manual prompt & code evaluation using `test_claude_webui_output.py`) |

### Datasets
- **HumanEval** (4 problems)  
- **MBPP** (2 problems)  
- **APPS** (2 problems)  
- **SWE-bench** (2 problems)  

**Total:** 10 problems evaluated per model.

### Prompting Strategies
1. **Baseline:** “Write ONLY the Python code without explanations.”  
2. **Chain-of-Thought:** “Think step-by-step: (1) Understand (2) Edge cases (3) Plan (4) Code.”  
3. **Self-Planning:** “Create a plan first, then implement.”  
4. **Self-Debugging:** “Write code, then mentally test with examples.”

---

## 🧠 Repository Structure

```
LLM-CodeGen-Assignment/
├── prompts/
│ ├── baseline.txt
│ ├── cot.txt
│ ├── self_planning.txt
│ ├── self_debugging.txt
│ ├── MBPP_25_refined.txt
│ └── MBPP_519_refined.txt
├── scripts/
│ ├── eval_gpt.py # Evaluate GPT models via OpenAI API
│ └── test_claude_webui_output.py # Evaluate Claude outputs copied from WebUI
├── results/
│ ├── gpt4o_result.json
│ ├── claude4.5_result.json
│ ├── refined_prompt_result.json
├── report/
│ └── Siyuan_Cen_LLM_CodeGen_Report.pdf
└── README.md
```

---

## 🚀 How to Run

### 1️⃣ Evaluate GPT Models via OpenAI API

**File:** `scripts/eval_gpt.py`

This script automatically sends prompts to GPT models via the OpenAI API, executes the returned code, and reports pass/fail results.

```bash
export OPENAI_API_KEY="your_api_key_here"
python scripts/eval_gpt.py
```

**Default model:** `gpt-4o`
 You can modify it to `"gpt-5"` or another model name inside the script.
 All results are saved under `results/results.json`.

------

### 2️⃣ Evaluate Claude Models via WebUI (Manual Process)

**File:** `scripts/test_claude_webui_output.py`

Claude Sonnet 4.5 does not have API access in this setup, so evaluation is done **manually** through Anthropic’s Web Interface.

#### Steps:

1. **Copy the correct prompt** (e.g., from `/prompts/MBPP_25_refined.txt`)
    Paste it directly into Claude’s WebUI input box.

2. **Let Claude generate the Python function.**
    Wait until it outputs the code (usually wrapped in triple backticks).

3. **Copy the output function** and save it into a local text file (e.g., `claude_MBPP_25.txt`).

4. **Run the testing script:**

   ```
   python scripts/test_claude_webui_output.py problems/MBPP_25.json claude_MBPP_25.txt
   ```

5. The script will:

   - Clean up any markdown fences (`python … `).
   - Execute the code safely in Python.
   - Run all dataset test cases.
   - Report which ones pass or fail.

#### Example Output

```
📝 Task ID: MBPP_25
🎯 Entry Point: find_Product
✅ PASSED 4/4 tests
```

This procedure was repeated for all 10 problems across the datasets.

------

## 📊 Evaluation Method

Each model’s generated code is executed against ground-truth test assertions defined in each dataset JSON.

- ✅ **PASS:** all assertions succeeded
- ❌ **FAIL:** at least one assertion failed

Overall **Pass@1** accuracy is calculated as:

\text{Pass@1} = \frac{\text{# Problems Passed}}{\text{# Total Problems}}

------

## 🧩 Innovation: Signature-Aware Prompting (SAP)

To fix dataset–prompt inconsistencies (especially in MBPP), the **Signature-Aware Prompting** method automatically injects explicit function signatures into prompts.

Example prompt modification:

```
You must use the function signature:
def find_Product(arr, n):
```

This refinement ensures the model outputs code compatible with the dataset’s expected interface.