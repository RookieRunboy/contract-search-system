from pathlib import Path
from typing import List, Tuple

from pdfToElasticSearch import PDFTextExtractor, JSONToElasticsearch


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    upload_dir = repo_root / "uploaded_contracts"

    if not upload_dir.exists():
        print(f"[ERROR] 上传目录不存在: {upload_dir}")
        return 1

    pdf_files = sorted(upload_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[WARN] 未在 {upload_dir} 中找到任何 PDF 文件")
        return 0

    print(f"[INFO] 准备仅更新元数据（不重新索引页面）: {len(pdf_files)} 个PDF ...")

    text_extractor = PDFTextExtractor()
    json_to_es = JSONToElasticsearch()

    success = 0
    failures: List[Tuple[str, str]] = []

    for pdf_path in pdf_files:
        try:
            data = pdf_path.read_bytes()
            pages = text_extractor.extract_text(data, pdf_path.stem)
            full_text = " ".join([p.get('text') or '' for p in pages])
            contract_name = pdf_path.stem
            ok = json_to_es.extract_and_update_metadata(contract_name, full_text)
            if ok:
                print(f"[OK] {pdf_path.name}: 元数据已更新")
                success += 1
            else:
                print(f"[SKIP] {pdf_path.name}: 未能更新（可能是LLM无结果）")
        except Exception as e:
            failures.append((pdf_path.name, str(e)))
            print(f"[FAIL] {pdf_path.name}: {e}")

    print("\n========== 汇总 ==========")
    print(f"成功: {success}")
    print(f"失败: {len(failures)}")
    if failures:
        for name, err in failures:
            print(f" - {name}: {err}")

    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())

