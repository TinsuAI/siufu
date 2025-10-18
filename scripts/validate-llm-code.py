#!/usr/bin/env python3
"""
Smoke test to validate Story 1.4 LLM code is syntactically correct
and has the expected structure.

This validates the code without requiring a full Docker environment.
"""
import ast
import sys
from pathlib import Path

def validate_file_syntax(file_path: Path) -> bool:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r') as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False

def check_class_exists(file_path: Path, class_name: str) -> bool:
    """Check if a class is defined in a file."""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return True
    return False

def check_function_exists(file_path: Path, function_name: str) -> bool:
    """Check if a function is defined in a file (including async functions)."""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return True
    return False

def main():
    backend_dir = Path(__file__).parent.parent / "backend"

    print("=" * 60)
    print("Story 1.4 LLM Implementation Validation")
    print("=" * 60)

    all_checks_passed = True

    # Check 1: OpenRouter client
    print("\n1️⃣  Checking OpenRouter client...")
    openrouter_file = backend_dir / "src/core/openrouter.py"
    if openrouter_file.exists():
        if validate_file_syntax(openrouter_file):
            if check_class_exists(openrouter_file, "OpenRouterClient"):
                print("   ✅ OpenRouterClient class exists")
            else:
                print("   ❌ OpenRouterClient class not found")
                all_checks_passed = False
        else:
            all_checks_passed = False
    else:
        print(f"   ❌ File not found: {openrouter_file}")
        all_checks_passed = False

    # Check 2: Extraction schemas
    print("\n2️⃣  Checking extraction schemas...")
    schemas_file = backend_dir / "src/schemas/extraction.py"
    if schemas_file.exists():
        if validate_file_syntax(schemas_file):
            required_classes = ["ExtractedData", "CompanyDetails", "ProductItem",
                              "ContainerDetails", "ShipmentDates"]
            for class_name in required_classes:
                if check_class_exists(schemas_file, class_name):
                    print(f"   ✅ {class_name} schema exists")
                else:
                    print(f"   ❌ {class_name} schema not found")
                    all_checks_passed = False
        else:
            all_checks_passed = False
    else:
        print(f"   ❌ File not found: {schemas_file}")
        all_checks_passed = False

    # Check 3: Prompts
    print("\n3️⃣  Checking prompt templates...")
    prompts_file = backend_dir / "src/services/prompts.py"
    if prompts_file.exists():
        if validate_file_syntax(prompts_file):
            if check_function_exists(prompts_file, "get_extraction_user_prompt"):
                print("   ✅ Prompt template functions exist")
            else:
                print("   ❌ Prompt functions not found")
                all_checks_passed = False
        else:
            all_checks_passed = False
    else:
        print(f"   ❌ File not found: {prompts_file}")
        all_checks_passed = False

    # Check 4: LLM Service
    print("\n4️⃣  Checking LLM service...")
    llm_service_file = backend_dir / "src/services/llm_service.py"
    if llm_service_file.exists():
        if validate_file_syntax(llm_service_file):
            if check_class_exists(llm_service_file, "LLMService"):
                print("   ✅ LLMService class exists")
                if check_function_exists(llm_service_file, "extract_structured_data"):
                    print("   ✅ extract_structured_data method exists")
                else:
                    print("   ❌ extract_structured_data method not found")
                    all_checks_passed = False
            else:
                print("   ❌ LLMService class not found")
                all_checks_passed = False
        else:
            all_checks_passed = False
    else:
        print(f"   ❌ File not found: {llm_service_file}")
        all_checks_passed = False

    # Check 5: Error handling
    print("\n5️⃣  Checking error handling...")
    errors_file = backend_dir / "src/core/errors.py"
    if errors_file.exists():
        if validate_file_syntax(errors_file):
            if check_class_exists(errors_file, "OpenRouterException"):
                print("   ✅ OpenRouterException exists")
            else:
                print("   ❌ OpenRouterException not found")
                all_checks_passed = False
        else:
            all_checks_passed = False
    else:
        print(f"   ❌ File not found: {errors_file}")
        all_checks_passed = False

    # Check 6: Unit tests
    print("\n6️⃣  Checking unit tests...")
    unit_test_file = backend_dir / "tests/unit/test_llm_service.py"
    if unit_test_file.exists():
        if validate_file_syntax(unit_test_file):
            print("   ✅ Unit tests file is valid Python")
        else:
            all_checks_passed = False
    else:
        print(f"   ❌ File not found: {unit_test_file}")
        all_checks_passed = False

    # Check 7: Integration tests
    print("\n7️⃣  Checking integration tests...")
    integration_test_file = backend_dir / "tests/integration/test_llm_integration.py"
    if integration_test_file.exists():
        if validate_file_syntax(integration_test_file):
            print("   ✅ Integration tests file is valid Python")
        else:
            all_checks_passed = False
    else:
        print(f"   ❌ File not found: {integration_test_file}")
        all_checks_passed = False

    # Check 8: Test fixtures
    print("\n8️⃣  Checking test fixtures...")
    fixtures_file = backend_dir / "tests/fixtures/openrouter.py"
    if fixtures_file.exists():
        if validate_file_syntax(fixtures_file):
            print("   ✅ Test fixtures file is valid Python")
        else:
            all_checks_passed = False
    else:
        print(f"   ❌ File not found: {fixtures_file}")
        all_checks_passed = False

    print("\n" + "=" * 60)
    if all_checks_passed:
        print("✅ ALL VALIDATION CHECKS PASSED")
        print("=" * 60)
        print("\nStory 1.4 implementation is syntactically correct and complete.")
        print("All required files, classes, and functions are present.")
        return 0
    else:
        print("❌ SOME VALIDATION CHECKS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
