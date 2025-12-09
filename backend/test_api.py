#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from llm_metadata_extractor import MetadataExtractor
import json

def test_api():
    try:
        extractor = MetadataExtractor()
        test_text = "甲方：北京科技有限公司，乙方：上海软件开发有限公司，合同金额：50万元，项目内容：软件开发服务，岗位：高级开发工程师，项目经理：张三，开发人员：李四、王五"
        
        print("测试完整的元数据提取功能...")
        print(f"测试文本: {test_text}")
        print("\n" + "="*50 + "\n")
        
        # 调用完整的提取方法
        result = extractor.extract_metadata(test_text)
        print("提取结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if result['success']:
            print("\n✅ 元数据提取成功！")
            print("提取的字段:")
            for key, value in result['metadata'].items():
                print(f"  {key}: {value}")
        else:
            print(f"\n❌ 元数据提取失败: {result['error']}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()