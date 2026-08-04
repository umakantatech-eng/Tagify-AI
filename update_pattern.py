import re

with open('backend/gemini_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'Pattern="Solid" and PnP="Solid".',
    'Pattern="Solid" and PnP="Solid". BUT if there is embroidery on the chest/neck, you MUST set Pattern="Embroidered" and PnP="Motif" (like Ethnic Motif).'
)

with open('backend/gemini_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
