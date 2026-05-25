with open("core/arkhe-js/arkhe.js", "r") as f:
    content = f.read()

new_func = """  enableTrapdoorCountermeasures(config = {}) {
    const safeConfig = config || {};
    this.strictMode = safeConfig.strictMode ?? this.strictMode;
    this.aiConfigScan = safeConfig.aiConfigScan ?? this.aiConfigScan;
    this.runtimeMonitor = safeConfig.runtimeMonitor ?? this.runtimeMonitor;
    this.ciGate = safeConfig.ciGate ?? this.ciGate;
    return this;
  }"""

import re
content = re.sub(r'  enableTrapdoorCountermeasures\(config = \{\}\) \{.*?  \}', new_func, content, flags=re.DOTALL)

with open("core/arkhe-js/arkhe.js", "w") as f:
    f.write(content)
