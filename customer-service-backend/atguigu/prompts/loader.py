from pathlib import Path


def load_prompt(prompt_file_name: str) -> str:
    """
    根据提示词模板文件的文件名加载模板内容到内存
    调用模型的时候渲染
    :param prompt_file_name:
    :return:
    """
    # 组装模板文件的path对象
    prompt_file_path = Path(__file__).resolve().parent / "jinja2" / f"{prompt_file_name}.jinja2"
    # 将模板的内容读取到内存中 还没有渲染占位符
    return prompt_file_path.read_text(encoding='utf_8')
