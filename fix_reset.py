import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add logic for daily reset
reset_logic = """
  const [usageCount, setUsageCount] = useState(() => {
    const today = new Date().toLocaleDateString();
    const lastReset = localStorage.getItem('lastResetDate');
    if (lastReset !== today) {
      localStorage.setItem('lastResetDate', today);
      localStorage.setItem('usageCount', '0');
      return 0;
    }
    return parseInt(localStorage.getItem('usageCount') || '0', 10);
  });
"""

content = re.sub(
    r'const \[usageCount, setUsageCount\] = useState\(\(\) => \{[^\}]+\}\);',
    reset_logic.strip(),
    content,
    flags=re.MULTILINE
)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
