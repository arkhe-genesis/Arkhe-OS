import os

with open('test/integration/oracle_test.go', 'r') as f:
    content = f.read()

content = content.replace('{consistent: false, minScore: 0.0, shouldHaveParadox: false},', '{consistent: false, minScore: 0.0, shouldHaveParadox: true},')
content = content.replace('fmt.Printf("Checks: %+v\\n", report.Checks)', '')

with open('test/integration/oracle_test.go', 'w') as f:
    f.write(content)
