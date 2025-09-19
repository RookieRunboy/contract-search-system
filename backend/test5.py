# 测试mineru能否使用
from mineru.backend.pipeline.pipeline_analyze import doc_analyze
from pathlib import Path
import json

pdf_path = Path("2.pdf")

# 读取 PDF 字节
with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

# 运行分析
results = doc_analyze(
    [pdf_path],           # 注意这里要传入列表
    lang_list=["ch"],
    table_enable=True,
    formula_enable=False
)

# 第0个元素是页面列表
page_results = results[0]

all_content_list = []

for page_list in page_results:
    for page_dict in page_list:
        # 提取 category_id==15 的文本项
        text_items = [
            item for item in page_dict.get("layout_dets", [])
            if item.get("category_id") == 15 and "text" in item
        ]

        # 按坐标排序：先按 y（垂直位置），再按 x（水平位置）
        sorted_items = sorted(
            text_items,
            key=lambda x: (x["poly"][1], x["poly"][0])  # 左上角坐标
        )

        # 只保留文本
        content_list = [item["text"] for item in sorted_items]
        all_content_list.append(content_list)

# 保存为 JSON
with open("content_list.json", "w", encoding="utf-8") as f:
    json.dump(all_content_list, f, ensure_ascii=False, indent=2)

print(f"提取完成，共 {len(all_content_list)} 页")
