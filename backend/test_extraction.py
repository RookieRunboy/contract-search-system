"""
测试文件名编码提取逻辑

此脚本用于验证 contractApi.py 中 _extract_codes_from_filename 函数的正确性。
测试各种文件名格式，特别是连字符分隔且编码位于任意位置的情况。
"""

import re
from pathlib import Path
from typing import Dict, Optional


def _extract_codes_from_filename(filename: str) -> Dict[str, Optional[str]]:
    """
    从文件名中提取合同编码和CIR编码。
    
    支持的命名模式：
    1. [合同编码]-[CIR编码]合同名.pdf (方括号格式)
    2. [合同编码]合同名.pdf
    3. [CIR编码]合同名.pdf
    4. 合同编码-CIR编码-合同名.pdf (无方括号格式，编码可位于任意位置)
    5. 合同名.pdf (无编码)
    
    Returns:
        Dict with 'contract_code' and 'cir_code' keys, values may be None
    """
    result: Dict[str, Optional[str]] = {
        "contract_code": None,
        "cir_code": None,
    }
    
    if not filename:
        return result
    
    base_name = Path(filename).stem
    
    # CIR 编码正则: 以 CIR 开头（不区分大小写），后接数字
    cir_pattern = re.compile(r'^cir\d+$', re.IGNORECASE)
    # 合同编码正则: 以字母开头，后接数字
    contract_code_pattern = re.compile(r'^[A-Za-z]\d+$')
    
    def classify_code(code: str) -> str:
        code_stripped = code.strip()
        if cir_pattern.match(code_stripped):
            return 'cir'
        if contract_code_pattern.match(code_stripped):
            return 'contract'
        return 'unknown'
    
    def assign_code(code: str) -> None:
        """根据编码类型分配到结果中（第一个匹配的优先）"""
        code_type = classify_code(code)
        if code_type == 'cir' and result["cir_code"] is None:
            result["cir_code"] = code
        elif code_type == 'contract' and result["contract_code"] is None:
            result["contract_code"] = code
    
    # 模式A: 方括号格式 [Code1]-[Code2]Name
    pattern_two_brackets = r'^\[([^\]]+)\]-\[([^\]]+)\]'
    match_two_brackets = re.match(pattern_two_brackets, base_name)
    if match_two_brackets:
        assign_code(match_two_brackets.group(1).strip())
        assign_code(match_two_brackets.group(2).strip())
        return result
    
    # 模式B: 方括号格式 [Code]Name
    pattern_one_bracket = r'^\[([^\]]+)\]'
    match_one_bracket = re.match(pattern_one_bracket, base_name)
    if match_one_bracket:
        assign_code(match_one_bracket.group(1).strip())
        return result
    
    # 模式C: 无方括号格式 - 用连字符分隔
    # 扫描所有片段以识别编码（编码可位于文件名任意位置）
    parts = base_name.split('-')
    for part in parts:
        part_stripped = part.strip()
        if part_stripped:
            assign_code(part_stripped)
        # 如果两种编码都已找到，可以提前结束
        if result["contract_code"] is not None and result["cir_code"] is not None:
            break
    
    # 如果找到了任何编码，则返回
    if result["contract_code"] is not None or result["cir_code"] is not None:
        return result
    
    return result


def run_tests():
    """运行提取逻辑测试"""
    test_cases = [
        # (文件名, 期望的contract_code, 期望的cir_code)
        
        # 模式1: 方括号格式 [Code1]-[Code2]
        ("[C123456789]-[CIR987654321]合同文件.pdf", "C123456789", "CIR987654321"),
        ("[CIR123456]-[A999888]合同说明.pdf", "A999888", "CIR123456"),
        
        # 模式2: 单方括号 - 合同编码
        ("[B555444333]采购合同.pdf", "B555444333", None),
        
        # 模式3: 单方括号 - CIR编码
        ("[CIR111222333]服务合同.pdf", None, "CIR111222333"),
        
        # 模式4: 连字符分隔 - 编码在开头
        ("C500000240806019-CIR500000240809005-合同名称.pdf", "C500000240806019", "CIR500000240809005"),
        
        # 模式4: 连字符分隔 - 编码位于中间（关键测试场景）
        ("Project-C500000240806019-CIR500000240809005.pdf", "C500000240806019", "CIR500000240809005"),
        ("FY24-ProjectName-C123456789-CIR987654321-Customer.pdf", "C123456789", "CIR987654321"),
        
        # 模式4: 复杂文件名（多个连字符）
        (
            "C500000240806019-CIR500000240809005-FY24运通环球天津PO-GBS China-Work Order-Han Wanhui(renew)-20250506-20251231-运通环球商业服务有限公司-313200.pdf",
            "C500000240806019",
            "CIR500000240809005"
        ),
        
        # 模式4: 只有合同编码
        ("Project-A888777666-Description.pdf", "A888777666", None),
        
        # 模式4: 只有CIR编码
        ("Project-CIR444555666-Description.pdf", None, "CIR444555666"),
        
        # 模式4: 编码位于文件名末尾
        ("描述信息-Project-C111222333.pdf", "C111222333", None),
        
        # 模式5: 无编码
        ("普通合同文件.pdf", None, None),
        ("Some-Random-FileName.pdf", None, None),
        
        # 边界情况: 多个可能的合同编码（应该选第一个）
        ("A111111111-B222222222-Description.pdf", "A111111111", None),
        
        # 边界情况: 多个可能的CIR编码（应该选第一个）
        ("CIR111111111-CIR222222222-Description.pdf", None, "CIR111111111"),
    ]
    
    print("=" * 60)
    print("文件名编码提取测试")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for filename, expected_contract, expected_cir in test_cases:
        result = _extract_codes_from_filename(filename)
        actual_contract = result["contract_code"]
        actual_cir = result["cir_code"]
        
        is_pass = (actual_contract == expected_contract and actual_cir == expected_cir)
        
        if is_pass:
            passed += 1
            status = "✓ PASS"
        else:
            failed += 1
            status = "✗ FAIL"
        
        # 截断过长文件名以便于展示
        display_name = filename[:50] + "..." if len(filename) > 50 else filename
        print(f"\n{status}: {display_name}")
        print(f"  期望: contract={expected_contract}, cir={expected_cir}")
        print(f"  实际: contract={actual_contract}, cir={actual_cir}")
    
    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
