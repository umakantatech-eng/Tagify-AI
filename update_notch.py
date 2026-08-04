import re

with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "Notch: Starts with a Round or Mandarin collar at the top/back, BUT has a small V-shaped slit or cut out in the front center. (Collar + V-slit = Notch). DO NOT call this V-neck.",
    "Notch: Has a small, sharp V-shaped slit in the front center of an otherwise round neck. It does NOT need to have a collar at the back. DO NOT call this Round."
)

content = content.replace(
    "Round: A simple, perfectly continuous circular curve. If there is ANY tiny V-cut or slit, it is NOT Round, it is Notch.",
    "Round: A perfectly continuous circular curve. If there is ANY tiny V-cut or slit, it is NOT Round, it is Notch."
)

with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
