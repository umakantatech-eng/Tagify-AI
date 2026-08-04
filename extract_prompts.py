import re

with open('backend/old_gemini_service.py', 'rb') as f:
    old_raw = f.read()
try:
    old_code = old_raw.decode('utf-16')
except UnicodeDecodeError:
    old_code = old_raw.decode('utf-8', errors='ignore')

with open('backend/gemini_service.py', 'rb') as f:
    new_raw = f.read()
new_code = new_raw.decode('utf-8', errors='ignore')

old_prompt = re.search(r'SYSTEM_INSTRUCTION = """(.*?)"""', old_code, re.DOTALL)
new_prompt = re.search(r'SYSTEM_INSTRUCTION = """(.*?)"""', new_code, re.DOTALL)

if old_prompt and new_prompt:
    with open('prompts_comparison.md', 'w', encoding='utf-8') as f:
        f.write("# Prompts Comparison\n\n")
        f.write("## New Prompt (Current)\n```text\n")
        f.write(new_prompt.group(1).strip())
        f.write("\n```\n\n## Old Prompt (Previous)\n```text\n")
        f.write(old_prompt.group(1).strip())
        f.write("\n```\n")
