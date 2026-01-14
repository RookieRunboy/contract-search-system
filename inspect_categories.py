import sys
import os
from pathlib import Path

# 添加 backend 到 path 以导入模块
sys.path.append(os.path.abspath("backend"))

try:
    from customer_category_loader import CustomerCategoryLookup
except ImportError:
    # 尝试直接导入（如果在 backend 下运行）
    try:
        from backend.customer_category_loader import CustomerCategoryLookup
    except ImportError:
        print("无法导入 customer_category_loader，请检查路径")
        sys.exit(1)

# 无论当前在哪，先找到根目录下的白名单
excel_path = Path("金融客户白名单.xlsx").resolve()
print(f"Loading from: {excel_path}")

if not excel_path.exists():
    print("文件不存在！")
    sys.exit(1)

try:
    loader = CustomerCategoryLookup(str(excel_path))
    # 强制刷新以加载
    loader.refresh() 
    hierarchy = loader.get_category_hierarchy()
    
    print("\n================ 分类层级概览 ================")
    if not hierarchy:
        print("(空)")
    
    level1_count = 0
    total_level2_count = 0
    
    for level1, level2_list in hierarchy.items():
        level1_count += 1
        count = len(level2_list)
        total_level2_count += count
        
        print(f"\n一级分类: 【{level1}】")
        if level2_list:
            # 打印所有二级分类，方便用户查看
            print(f"  └─ 二级分类 ({count}个): {', '.join(level2_list)}")
        else:
            print("  └─ (无二级分类)")
            
    print(f"\n================ 统计 ================")
    print(f"一级分类总数: {level1_count}")
    print(f"二级分类总数: {total_level2_count}")
    
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
