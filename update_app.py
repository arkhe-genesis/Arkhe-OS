import re

with open('src/App.tsx', 'r') as f:
    text = f.read()

# Add to activePanel state logic or main menu
text = text.replace(
    "import MolecularCommunicationPanel from './components/MolecularCommunicationPanel';",
    "import MolecularCommunicationPanel from './components/MolecularCommunicationPanel';\nimport ArkheV288 from './components/ArkheV288';"
)

text = re.sub(
    r"type PanelType = 'simulation'",
    "type PanelType = 'arkhe-v288' | 'simulation'",
    text
)

text = text.replace(
    '          {activePanel === \'simulation\' && (',
    '          {activePanel === \'arkhe-v288\' && (\n            <div className="absolute inset-0 z-50 bg-black">\n              <ArkheV288 />\n            </div>\n          )}\n          {activePanel === \'simulation\' && ('
)

# Add to sidebar menu if exists
menu_item = """
            <button
              onClick={() => setActivePanel('arkhe-v288')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                activePanel === 'arkhe-v288' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <Video className="w-5 h-5" />
              <span>ArkheV288</span>
            </button>
"""

# Find where navigation happens and append button manually.
# For example, look for the 'intelligence' button and put it right after.
if "onClick={() => setActivePanel('intelligence')}" in text:
    target = """<button
              onClick={() => setActivePanel('intelligence')}"""
    text = text.replace(target, menu_item.strip() + '\n              ' + target)

with open('src/App.tsx', 'w') as f:
    f.write(text)
