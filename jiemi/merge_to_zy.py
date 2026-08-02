import os
import json  # 强制使用标准库 json 写入，确保输出 100% 标准
import json5  # 用 json5 读取，以兼容你原本带注释的源文件
import chardet

TVBOX_FILE = "tvbox_config.json"
MOYU_FILE = "moyu.json"
OUTPUT_FILE = "zy.json"

def detect_encoding(file_path):
    if not os.path.exists(file_path):
        return "utf-8"
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
        result = chardet.detect(raw_data)
        return result['encoding'] or "utf-8"

def read_json_file(file_path):
    if not os.path.exists(file_path):
        print(f"[-] 未找到文件: {file_path}")
        return None
    encoding = detect_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            # 读取时用 json5，完美兼容所有不标准格式、注释等
            return json5.load(f)
    except Exception as e:
        print(f"[-] 读取 {file_path} 失败: {e}")
        return None

def write_standard_json(file_path, data, reference_file):
    encoding = detect_encoding(reference_file)
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            # 关键：强制使用标准 json 库 dump！
            # 这会强制给所有 keys 和 values 加上双引号，并生成最标准的大括号
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[+] 成功生成/更新标准文件: {file_path}")
    except Exception as e:
        print(f"[-] 写入 {file_path} 失败: {e}")

def merge_sites():
    print("[*] 开始读取文件并准备合并...")
    tvbox_data = read_json_file(TVBOX_FILE)
    moyu_data = read_json_file(MOYU_FILE)

    if tvbox_data is None or moyu_data is None:
        print("[-] 合并中止：源文件读取失败。")
        exit(1)

    # 提取 sites 列表
    tvbox_sites = tvbox_data.get("sites", [])
    moyu_sites = moyu_data.get("sites", [])

    if not isinstance(tvbox_sites, list) or not isinstance(moyu_sites, list):
        print("[-] 错误: 'sites' 字段不是列表格式！")
        exit(1)

    # 合并 sites：tvbox 在前，moyu 在后，顺序保持不变
    merged_sites = tvbox_sites + moyu_sites

    # 封装为标准的 Python 字典对象（自动带有外层 {}）
    output_data = {
        "sites": merged_sites
    }

    # 写入到全新的 zy.json 中
    write_standard_json(OUTPUT_FILE, output_data, TVBOX_FILE)
    print("[*] 合并完成！")

if __name__ == "__main__":
    merge_sites()
