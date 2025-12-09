from pathlib import Path
from types import SimpleNamespace
from io import BytesIO
from typing import List, Tuple

from pdfToElasticSearch import PdfToElasticsearch


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

    print(f"[INFO] 准备重新索引 {len(pdf_files)} 个PDF 文件到 Elasticsearch ...")

    pdf_to_es = PdfToElasticsearch()

    success = 0
    failures: List[Tuple[str, str]] = []

    for pdf_path in pdf_files:
        try:
            data = pdf_path.read_bytes()
            fake_upload = SimpleNamespace(
                file=BytesIO(data),
                filename=pdf_path.name,
                content_type='application/pdf',
            )

            result = pdf_to_es.start_process(fake_upload)
            print(f"[OK] {pdf_path.name}: {result}")
            success += 1
        except Exception as e:
            failures.append((pdf_path.name, str(e)))
            print(f"[FAIL] {pdf_path.name}: {e}")

    print("\n========== 汇总 ==========")
    print(f"成功: {success}")
    print(f"失败: {len(failures)}")
    if failures:
        for name, err in failures:
            print(f" - {name}: {err}")

    # 返回非零表示有失败，便于CI/脚本判断
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())

