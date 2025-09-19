import json
from pathlib import Path
import requests
import argparse

BASE_URL = "http://172.16.5.31:8006"  # 可改为本地 http://localhost:8006


def check_system(base_url: str = BASE_URL):
    url = f"{base_url}/system/elasticsearch"
    try:
        resp = requests.get(url, timeout=30)
        print("[system] status:", resp.status_code)
        print(resp.text)
    except Exception as e:
        print("[system] error:", e)


def upload_pdf(pdf_path: str | Path, base_url: str = BASE_URL):
    url = f"{base_url}/document/add"
    pdf_path = Path(pdf_path)
    assert pdf_path.exists(), f"文件不存在: {pdf_path}"
    try:
        with pdf_path.open("rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            resp = requests.post(url, files=files, timeout=600)
        print("[upload] status:", resp.status_code)
        print(resp.text)
        return resp
    except Exception as e:
        print("[upload] error:", e)
        return None


def search(query: str, base_url: str = BASE_URL, **kwargs):
    url = f"{base_url}/document/search"
    params = {"query": query}
    params.update(kwargs)
    try:
        resp = requests.get(url, params=params, timeout=60)
        print("[search] status:", resp.status_code)
        try:
            print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
        except Exception:
            print(resp.text)
        return resp
    except Exception as e:
        print("[search] error:", e)
        return None


essential_note = (
    "删除接口现在兼容：可传 'example' 或 'example.pdf'，甚至 '/path/example.pdf'；后端会自动归一化为不带扩展名的文件名来匹配。\n"
    "因此你可以使用示例：DELETE /document/delete?filename=example 或 example.pdf 都可以。"
)


def delete_by_filename(filename_or_path: str, base_url: str = BASE_URL):
    url = f"{base_url}/document/delete"
    params = {"filename": filename_or_path}
    try:
        resp = requests.delete(url, params=params, timeout=60)
        print("[delete] status:", resp.status_code)
        print(resp.text)
        return resp
    except Exception as e:
        print("[delete] error:", e)
        return None


def get_cli_spec():
    """返回机器可读的 CLI 能力描述，便于智能体自动发现和调用。"""
    return {
        "name": "contract-retrieval-cli",
        "version": "1.0.0",
        "base_url_default": BASE_URL,
        "actions": {
            "check": {
                "description": "检查后端与 Elasticsearch 状态",
                "method": "GET",
                "endpoint": "/system/elasticsearch",
                "params": []
            },
            "upload": {
                "description": "上传一个或多个 PDF 文件并入库（解析+向量化）",
                "method": "POST",
                "endpoint": "/document/add",
                "params": [
                    {"name": "file", "type": "file", "multiple": True, "required": True}
                ]
            },
            "search": {
                "description": "文档检索（混合：向量+关键词）",
                "method": "GET",
                "endpoint": "/document/search",
                "params": [
                    {"name": "query", "type": "string", "required": True},
                    {"name": "top_k", "type": "integer", "required": False, "default": 3}
                ]
            },
            "delete": {
                "description": "删除文档（兼容 stem、带扩展名或完整路径）",
                "method": "DELETE",
                "endpoint": "/document/delete",
                "params": [
                    {"name": "filename", "type": "string", "multiple": True, "required": True,
                     "note": "可传 'example'、'example.pdf' 或 '/path/example.pdf'，后端会自动归一化为 contractName"}
                ]
            }
        },
        "global_options": [
            {"name": "url", "type": "string", "default": BASE_URL, "alias": ["-u"], "description": "后端基础地址"}
        ],
        "examples": [
            "python test_api_local.py --check",
            "python test_api_local.py -u http://localhost:8006 --check",
            "python test_api_local.py -u http://localhost:8006 -U ./a.pdf ./b.pdf",
            "python test_api_local.py -u http://localhost:8006 -q '付款条款' --top-k 5",
            "python test_api_local.py -u http://localhost:8006 -d a a.pdf ./案例合同/a.pdf",
            "python test_api_local.py -u http://localhost:8006 --check -U ./a.pdf ./b.pdf -q '付款条款' --top-k 10 -d a b"
        ]
    }


def main_cli():
    parser = argparse.ArgumentParser(description="合同检索系统一键联调脚本")
    parser.add_argument("--url", "-u", default=BASE_URL, help="后端服务地址，默认读取脚本内 BASE_URL")
    parser.add_argument("--check", action="store_true", help="仅检查系统状态")
    parser.add_argument("--upload", "-U", nargs="+", help="上传一个或多个PDF文件路径")
    parser.add_argument("--query", "-q", help="搜索关键词")
    parser.add_argument("--top-k", type=int, default=3, dest="top_k", help="搜索返回条数，默认3")
    parser.add_argument("--delete", "-d", nargs="+", help="按文件名删除（可传stem、带扩展名或包含路径）")
    parser.add_argument("--spec", action="store_true", help="输出 JSON 能力描述后退出")

    args = parser.parse_args()

    # 输出机器可读能力描述并退出
    if args.spec:
        print(json.dumps(get_cli_spec(), ensure_ascii=False, indent=2))
        print("\n提示：可执行 `python test_api_local.py --spec` 获取机器可读的 CLI 能力清单，或查看项目根目录的 actions.json。\n")
        return

    # 如果没有传入任何动作参数，则执行原有的默认烟雾测试流程
    no_action = not any([args.check, args.upload, args.query, args.delete])

    if no_action:
        # 1) 自检后端/ES状态
        check_system(args.url)

        # 2) 选择一个要上传的本地PDF
        sample_pdf = Path("./案例合同/CIR500000220516017-银华基金信息系统技术开发服务合同-2022外包-银华基金管理股份有限公司-3263400-完整版.pdf")
        if not sample_pdf.exists():
            print(f"示例PDF不存在，请修改路径: {sample_pdf}")
        else:
            # 3) 上传PDF（入库+向量化）
            upload_pdf(sample_pdf, base_url=args.url)

        # 4) 搜索
        search("银华基金", base_url=args.url, top_k=3)

        # 5) 删除说明（默认不执行删除）
        print("\n" + essential_note + "\n")
        print("如需删除，请使用 --delete 参数，例如：--delete example 或 example.pdf")
        print("\n提示：可执行 `python test_api_local.py --spec` 获取机器可读的 CLI 能力清单，或查看项目根目录的 actions.json。\n")
        return

    # 有动作参数时，按顺序执行
    if args.check:
        check_system(args.url)

    if args.upload:
        for p in args.upload:
            try:
                upload_pdf(p, base_url=args.url)
            except AssertionError as e:
                print(e)

    if args.query:
        search(args.query, base_url=args.url, top_k=args.top_k)

    if args.delete:
        print("\n" + essential_note + "\n")
        for name in args.delete:
            delete_by_filename(name, base_url=args.url)


if __name__ == "__main__":
    main_cli()