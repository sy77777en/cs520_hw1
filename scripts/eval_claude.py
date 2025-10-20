"""
test_claude_webui_output.py
用于测试从Claude Web UI复制的代码
"""

import json
import sys


def clean_code(code: str) -> str:
    """清理代码（移除markdown标记）"""
    lines = code.split('\n')
    # 移除开头的 ```python 或 ```
    while lines and lines[0].strip().startswith('```'):
        lines = lines[1:]
    # 移除结尾的 ```
    while lines and lines[-1].strip() == '```':
        lines = lines[:-1]
    return '\n'.join(lines)


def test_humaneval(problem_file: str, generated_code: str):
    """测试HumanEval问题"""
    with open(problem_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📝 Task ID: {data.get('task_id', 'Unknown')}")
    print(f"🎯 Entry Point: {data['entry_point']}")
    
    env = {}
    try:
        code = clean_code(generated_code)
        print("\n🔧 Executing generated code...")
        exec(code, env)
        
        print("🧪 Running test cases...")
        exec(data["test"], env)
        env["check"](env[data["entry_point"]])
        
        print("\n" + "="*60)
        print("✅ ✅ ✅  ALL TESTS PASSED!  ✅ ✅ ✅")
        print("="*60)
        return True
    except AssertionError as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED - Assertion Error")
        print("="*60)
        print(f"Error: {e}")
        return False
    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED - Execution Error")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error: {e}")
        return False


def test_mbpp(problem_file: str, generated_code: str):
    """测试MBPP问题"""
    with open(problem_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📝 Task ID: {data.get('task_id', 'Unknown')}")
    print(f"🎯 Entry Point: {data['entry_point']}")
    
    env = {}
    try:
        code = clean_code(generated_code)
        print("\n🔧 Executing generated code...")
        exec(code, env)
        
        print("🧪 Running test cases...")
        for i, test in enumerate(data["test_list"], 1):
            exec(test, env)
            print(f"   Test {i}/{len(data['test_list'])} passed ✓")
        
        print("\n" + "="*60)
        print("✅ ✅ ✅  ALL TESTS PASSED!  ✅ ✅ ✅")
        print("="*60)
        return True
    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED at test case {i}")
        print("="*60)
        print(f"Error: {e}")
        return False
    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED - Execution Error")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error: {e}")
        return False


def test_apps(problem_file: str, generated_code: str):
    """测试APPS问题"""
    with open(problem_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📝 Prompt: {data.get('prompt', 'Unknown')[:100]}...")
    
    env = {}
    try:
        code = clean_code(generated_code)
        print("\n🔧 Executing generated code...")
        exec(code, env)
        
        # 获取函数
        func_name = data.get("entry_point", "")
        if not func_name and "starter_code" in data:
            func_name = data["starter_code"].split("def ")[1].split("(")[0].strip()
        
        if func_name and func_name in env:
            func = env[func_name]
        else:
            func = [v for v in env.values() if callable(v)][-1]
        
        print(f"🎯 Testing function: {func.__name__}")
        print("🧪 Running test cases...")
        
        # 运行测试
        for i, (inp, expected) in enumerate(zip(data["inputs"], data["outputs"]), 1):
            inp_val = eval(inp[0])
            expected_val = expected[0]
            result = func(inp_val)
            if result != expected_val:
                raise AssertionError(f"Test {i}: Expected {expected_val}, got {result}")
            print(f"   Test {i}/{len(data['inputs'])} passed ✓")
        
        print("\n" + "="*60)
        print("✅ ✅ ✅  ALL TESTS PASSED!  ✅ ✅ ✅")
        print("="*60)
        return True
    except AssertionError as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED")
        print("="*60)
        print(f"Error: {e}")
        return False
    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED - Execution Error")
        print("="*60)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error: {e}")
        return False


def main():
    print("="*60)
    print("       Claude Web UI Output Tester")
    print("="*60)
    
    # 从命令行获取参数，或手动输入
    if len(sys.argv) >= 2:
        problem_file = sys.argv[1]
    else:
        problem_file = input("\n📁 Enter problem JSON file path: ").strip()
    
    # 检测数据集类型
    fname_upper = problem_file.upper()
    if "HE" in fname_upper or "HUMANEVAL" in fname_upper:
        dataset_type = "humaneval"
    elif "MBPP" in fname_upper:
        dataset_type = "mbpp"
    elif "APPS" in fname_upper:
        dataset_type = "apps"
    else:
        print("\n❓ Cannot auto-detect dataset type. Please specify:")
        print("1. HumanEval")
        print("2. MBPP")
        print("3. APPS")
        choice = input("Enter choice (1/2/3): ").strip()
        dataset_type = {
            "1": "humaneval",
            "2": "mbpp",
            "3": "apps"
        }.get(choice, "humaneval")
    
    print(f"\n📊 Dataset: {dataset_type.upper()}")
    print(f"📁 Problem file: {problem_file}")
    print("\n" + "="*60)
    print("📋 Paste the code from Claude below")
    print("   (End with Ctrl+D on Mac/Linux or Ctrl+Z then Enter on Windows)")
    print("="*60 + "\n")
    
    # 读取多行输入
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    generated_code = '\n'.join(lines)
    
    if not generated_code.strip():
        print("\n❌ No code provided!")
        return
    
    print("\n" + "="*60)
    print("🔍 Testing your code...")
    print("="*60)
    
    # 运行测试
    if dataset_type == "humaneval":
        success = test_humaneval(problem_file, generated_code)
    elif dataset_type == "mbpp":
        success = test_mbpp(problem_file, generated_code)
    elif dataset_type == "apps":
        success = test_apps(problem_file, generated_code)
    
    print("\n" + "="*60)
    if success:
        print("🎉 Result: PASS")
    else:
        print("💔 Result: FAIL")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()