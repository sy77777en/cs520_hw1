"""
eval_gpt.py - Enhanced with Improved Prompts
---------------------------------
Addresses function naming and input format issues
---------------------------------
"""

import os
import json
from tqdm import tqdm
from openai import OpenAI
from datetime import datetime
import re


# --------------- Setup -------------------
client = OpenAI(api_key="")
MODEL_NAME = "gpt-4o"
DATA_DIR = "problems"
RESULT_PATH = f"results_{MODEL_NAME.replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
MAX_TOKENS = 8192
TEMPERATURE = 0.0


# ---------------- Prompting Strategies ---------------- #
PROMPTING_STRATEGIES = {
    "baseline": {
        "system": "You are a professional Python programmer. Write only valid Python code for the given function. Do not include explanations, markdown, or text outside the code block.",
        "user_template": "{prompt}"
    },
    
    "baseline_improved": {
        "system": "You are a professional Python programmer. Write only valid Python code for the given function. Do not include explanations, markdown, or text outside the code block.",
        "user_template": """{prompt}

CRITICAL REQUIREMENTS:
- Use the EXACT function name specified in the problem (do not rename it)
- Use the EXACT function signature specified in the problem
- If the problem specifies parameters, include ALL of them
- For competitive programming problems, accept input as function parameters, NOT from stdin"""
    },
    
    "chain_of_thought": {
        "system": "You are a professional Python programmer. Think step-by-step before writing code.",
        "user_template": """Problem: {prompt}

Let's solve this step by step:
1. First, understand what the function should do
2. Think about edge cases
3. Plan the algorithm
4. Write the code

Now provide your solution with only the Python code:"""
    },
    
    "self_planning": {
        "system": "You are a professional Python programmer. First create a plan, then implement it.",
        "user_template": """Problem: {prompt}

Before writing code, create a plan:
- What is the input/output?
- What are the key steps?
- What edge cases exist?

Then write the implementation code only:"""
    },
    
    "self_debugging": {
        "system": "You are a professional Python programmer. Write code and then verify it mentally.",
        "user_template": """Problem: {prompt}

Write the code, then mentally test it with the provided examples to ensure correctness. Consider edge cases."""
    },
}


# ---------------- Dataset-Specific Prompt Builders ---------------- #
def build_mbpp_prompt(text: str, entry_point: str) -> str:
    """Build MBPP-specific prompt with explicit naming requirements."""
    return f"""{text}

CRITICAL REQUIREMENTS:
- Function name MUST be exactly: {entry_point}
- Do NOT use descriptive names like "product_of_..." or "calculate_..."
- Use the EXACT function name: {entry_point}
- Check if the problem specifies additional parameters beyond the array

Provide the complete function implementation."""


def build_apps_prompt(prompt: str, entry_point: str = None) -> str:
    """Build APPS-specific prompt with explicit input format requirements."""
    base_prompt = f"""{prompt}

CRITICAL REQUIREMENTS:
- Your function MUST accept input as a PARAMETER, NOT from stdin
- Do NOT use sys.stdin.read, sys.stdin.readline, or input()
- The test framework will call your function with data passed as an argument
- Parse the input parameter directly (e.g., input_data[0], input_data[1:])"""
    
    if entry_point:
        base_prompt += f"\n- Function name must be: {entry_point}"
    
    return base_prompt + "\n\nProvide the complete function implementation."


# ---------------- Dataset Detection ---------------- #
def detect_dataset(filename: str) -> str:
    """Detect dataset type from filename."""
    fname_upper = filename.upper()
    if "HE" in fname_upper or "HUMANEVAL" in fname_upper:
        return "HumanEval"
    elif "MBPP" in fname_upper:
        return "MBPP"
    elif "APPS" in fname_upper:
        return "APPS"
    elif "SWE" in fname_upper:
        return "SWE"
    return "Unknown"


# ---------------- GPT Call ---------------- #
def call_gpt(prompt: str, strategy: str = "baseline") -> str:
    """Call GPT model with specified prompting strategy."""
    strategy_config = PROMPTING_STRATEGIES[strategy]
    user_prompt = strategy_config["user_template"].format(prompt=prompt)
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": strategy_config["system"]},
            {"role": "user", "content": user_prompt},
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content.strip()


# ---------------- Code Cleaning Function ---------------- #
def clean_code(code: str) -> str:
    """Extract pure Python code from GPT output."""
    # Method 1: Find code blocks
    code_block_pattern = r'```(?:python)?\s*\n(.*?)\n```'
    matches = re.findall(code_block_pattern, code, re.DOTALL)
    
    if matches:
        return matches[-1].strip()
    
    # Method 2: Extract lines starting with def/import
    lines = code.split('\n')
    code_lines = []
    in_code = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip markdown and explanation text
        if stripped.startswith('#') and any(word in stripped for word in ['Step', 'Plan', 'Example', 'Note']):
            continue
        if any(stripped.startswith(prefix) for prefix in ['##', '###', '**', 'To solve', 'Let\'s', 'Here\'s', 'Now,', 'The function', 'This implementation', 'CRITICAL']):
            continue
        
        # Detect code start
        if stripped.startswith(('def ', 'import ', 'from ', 'class ')):
            in_code = True
        
        # Collect code lines
        if in_code:
            # Stop at explanation text
            if stripped and not stripped.startswith(('#', 'def', 'import', 'from', 'class', ' ', '\t', '@')) and \
               any(keyword in stripped.lower() for keyword in ['example usage', 'test case', 'output:', 'expected', 'explanation', 'mental', 'note:']):
                break
            code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return code.strip()


# ---------------- Evaluation Logic ---------------- #
def run_humaneval(entry_point: str, test_code: str, model_code: str) -> tuple[bool, str]:
    """Run HumanEval tests."""
    env = {}
    try:
        model_code = clean_code(model_code)
        exec(model_code, env)
        exec(test_code, env)
        env["check"](env[entry_point])
        return True, ""
    except Exception as e:
        return False, str(e)


def run_mbpp(entry_point: str, test_list: list, model_code: str) -> tuple[bool, str]:
    """Run MBPP tests."""
    env = {}
    try:
        model_code = clean_code(model_code)
        exec(model_code, env)
        for t in test_list:
            exec(t, env)
        return True, ""
    except Exception as e:
        return False, str(e)


def run_apps(data: dict, model_code: str) -> tuple[bool, str]:
    """Run APPS tests."""
    env = {}
    try:
        model_code = clean_code(model_code)
        exec(model_code, env)
        
        func_name = data.get("entry_point", "")
        if not func_name and "starter_code" in data:
            func_name = data["starter_code"].split("def ")[1].split("(")[0].strip()
        
        if func_name and func_name in env:
            func = env[func_name]
        else:
            func = [v for v in env.values() if callable(v)][-1]
        
        for inp, expected in zip(data["inputs"], data["outputs"]):
            inp_val = eval(inp[0])
            expected_val = expected[0]
            result = func(inp_val)
            if result != expected_val:
                raise AssertionError(f"Expected {expected_val}, got {result}")
        return True, ""
    except Exception as e:
        return False, str(e)


def run_swe(data: dict, model_code: str) -> tuple[bool, str]:
    """Run SWE-bench tests (simplified - syntax check only)."""
    try:
        model_code = clean_code(model_code)
        compile(model_code, '<string>', 'exec')
        return True, "SWE: Syntax valid"
    except Exception as e:
        return False, str(e)


# ---------------- Evaluation Dispatcher ---------------- #
def evaluate_task(data: dict, dataset: str, strategies: list) -> dict:
    """Evaluate task with multiple prompting strategies."""
    # Build dataset-specific prompts
    if dataset == "HumanEval":
        base_prompt = data.get("prompt", "")
    elif dataset == "MBPP":
        base_prompt = build_mbpp_prompt(
            data.get("text", ""),
            data.get("entry_point", "")
        )
    elif dataset == "APPS":
        base_prompt = build_apps_prompt(
            data.get("prompt", ""),
            data.get("entry_point", "")
        )
    elif dataset == "SWE":
        base_prompt = f"Problem: {data.get('problem_statement', '')}\n\nFix the issue."
    else:
        base_prompt = data.get("prompt") or data.get("text", "")
    
    results_per_strategy = {}
    
    # Test each strategy
    for strategy in strategies:
        # Use improved prompts for baseline, original for others
        if strategy == "baseline":
            # Test both original and improved baseline
            for variant in ["baseline", "baseline_improved"]:
                code = call_gpt(base_prompt, variant)
                
                # Run tests
                if dataset == "HumanEval":
                    passed, error = run_humaneval(data["entry_point"], data["test"], code)
                elif dataset == "MBPP":
                    passed, error = run_mbpp(data["entry_point"], data["test_list"], code)
                elif dataset == "APPS":
                    passed, error = run_apps(data, code)
                elif dataset == "SWE":
                    passed, error = run_swe(data, code)
                else:
                    passed, error = False, "Unknown dataset"
                
                strategy_name = variant if variant == "baseline_improved" else "baseline"
                results_per_strategy[strategy_name] = {
                    "passed": passed,
                    "error": error if not passed else "",
                    "code": code
                }
                
                # If baseline_improved passed, we're done
                if variant == "baseline_improved" and passed:
                    break
        else:
            code = call_gpt(base_prompt, strategy)
            
            # Run tests
            if dataset == "HumanEval":
                passed, error = run_humaneval(data["entry_point"], data["test"], code)
            elif dataset == "MBPP":
                passed, error = run_mbpp(data["entry_point"], data["test_list"], code)
            elif dataset == "APPS":
                passed, error = run_apps(data, code)
            elif dataset == "SWE":
                passed, error = run_swe(data, code)
            else:
                passed, error = False, "Unknown dataset"
            
            results_per_strategy[strategy] = {
                "passed": passed,
                "error": error if not passed else "",
                "code": code
            }
    
    return {
        "task_id": data.get("task_id", data.get("instance_id", "unknown")),
        "dataset": dataset,
        "prompt": base_prompt,
        "strategies": results_per_strategy
    }


# ---------------- Main Runner ---------------- #
def main():
    # Test both original and improved prompts
    strategies_to_test = ["baseline", "chain_of_thought", "self_planning", "self_debugging"]
    
    results = []
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]
    print(f"🧩 Found {len(files)} tasks in {DATA_DIR}/")
    print(f"🔬 Testing strategies: {', '.join(strategies_to_test)}")
    print(f"📝 Note: 'baseline' will test both original and improved versions\n")
    
    # Stats tracking (including baseline_improved)
    all_strategies = strategies_to_test + ["baseline_improved"]
    strategy_stats = {s: {"total": 0, "passed": 0} for s in all_strategies}
    dataset_stats = {}

    for fname in tqdm(files, desc="Evaluating"):
        path = os.path.join(DATA_DIR, fname)
        dataset = detect_dataset(fname)
        
        try:
            with open(path) as f:
                data = json.load(f)
            
            result = evaluate_task(data, dataset, strategies_to_test)
            result["filename"] = fname
            results.append(result)
            
            # Update stats
            if dataset not in dataset_stats:
                dataset_stats[dataset] = {s: {"total": 0, "passed": 0} for s in all_strategies}
            
            for strategy in result["strategies"].keys():
                strategy_stats[strategy]["total"] += 1
                dataset_stats[dataset][strategy]["total"] += 1
                
                if result["strategies"][strategy]["passed"]:
                    strategy_stats[strategy]["passed"] += 1
                    dataset_stats[dataset][strategy]["passed"] += 1
                    
        except Exception as e:
            print(f"\n⚠️  Error processing {fname}: {e}")

    # Save results
    with open(RESULT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "="*70)
    print(f"MODEL: {MODEL_NAME}")
    print("="*70)
    
    print("\n📊 Overall Strategy Performance:")
    for strategy in ["baseline", "baseline_improved"] + strategies_to_test[1:]:
        if strategy in strategy_stats and strategy_stats[strategy]["total"] > 0:
            stats = strategy_stats[strategy]
            acc = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
            marker = " ⭐ IMPROVED" if strategy == "baseline_improved" else ""
            print(f"   {strategy:20} {stats['passed']:3}/{stats['total']:3} ({acc:5.1f}%){marker}")
    
    # Show improvement
    if "baseline" in strategy_stats and "baseline_improved" in strategy_stats:
        baseline_acc = (strategy_stats["baseline"]["passed"] / strategy_stats["baseline"]["total"] * 100)
        improved_acc = (strategy_stats["baseline_improved"]["passed"] / strategy_stats["baseline_improved"]["total"] * 100)
        improvement = improved_acc - baseline_acc
        print(f"\n💡 Improvement: {improvement:+.1f} percentage points")
    
    print("\n📊 Per-Dataset Performance:")
    for dataset, strategies in sorted(dataset_stats.items()):
        print(f"\n   {dataset}:")
        for strategy in ["baseline", "baseline_improved"] + strategies_to_test[1:]:
            if strategy in strategies and strategies[strategy]["total"] > 0:
                stats = strategies[strategy]
                acc = (stats["passed"] / stats["total"] * 100)
                marker = " ⭐" if strategy == "baseline_improved" else ""
                print(f"      {strategy:20} {stats['passed']:3}/{stats['total']:3} ({acc:5.1f}%){marker}")
    
    print(f"\n🗂  Results saved to {RESULT_PATH}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()