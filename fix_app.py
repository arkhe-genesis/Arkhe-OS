import re

with open('src/App.tsx', 'r') as f:
    text = f.read()

# Add to navigation items array
navigation_item = "{ id: 'arkhe-v288', label: 'Arkhe v∞.288', icon: Video },"

if "const navigation = [" in text:
    target = "const navigation = ["
    text = text.replace(target, target + "\n    " + navigation_item)

with open('src/App.tsx', 'w') as f:
    f.write(text)
