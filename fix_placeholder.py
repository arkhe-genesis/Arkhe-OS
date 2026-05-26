with open('substrates/t/846_enterprise_architecture_bridge/substrato_846_enterprise_architecture_bridge.py', 'r') as f:
    content = f.read()

new_content = content.replace('cell = "846-SYS-FUNC"', 'cell = "846-SYST-HOW"')

with open('substrates/t/846_enterprise_architecture_bridge/substrato_846_enterprise_architecture_bridge.py', 'w') as f:
    f.write(new_content)
