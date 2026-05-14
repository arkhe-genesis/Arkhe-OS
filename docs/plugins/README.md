# ARKHE Plugin Development Guide

## Overview
ARKHE supports extensibility via plugins that add new languages, operators, or analysis modules. Plugins are dynamically loaded and sandboxed for security.

## Plugin Types

### 1. Language Plugins
Add support for new programming languages to the Polymath-Polyglot Parser.

**Interface (`LanguagePlugin` trait):**
```rust
pub trait LanguagePlugin: Send + Sync {
    fn name(&self) -> &str;
    fn version(&self) -> &str;
    fn grammar(&self) -> Result<Vec<u8>, PluginError>;
    fn tokenize(&self, source: &str) -> Result<Vec<u8>, PluginError>;
    fn parse(&self, source: &str) -> Result<Vec<u8>, PluginError>;
    fn transpile(&self, source: &str, target: &str) -> Result<String, PluginError>;
    fn verify(&self) -> Result<(), PluginError>;
}
```

**Example: Adding "MyLang" Support**
```rust
// mylang_plugin.rs
use arkhe_polyglot::plugins::{LanguagePlugin, PluginError};

pub struct MyLangPlugin;

impl LanguagePlugin for MyLangPlugin {
    fn name(&self) -> &str { "mylang" }
    fn version(&self) -> &str { "1.0.0" }

    fn grammar(&self) -> Result<Vec<u8>, PluginError> {
        // Return serialized grammar definition
        Ok(include_bytes!("mylang.grammar").to_vec())
    }

    fn tokenize(&self, source: &str) -> Result<Vec<u8>, PluginError> {
        // Implement lexer for MyLang
        // Return serialized tokens
        Ok(vec![]) // Placeholder
    }

    // ... implement other methods
    fn verify(&self) -> Result<(), PluginError> { Ok(()) }
}

// Export for dynamic loading
#[no_mangle]
pub extern "C" fn create_plugin() -> *mut dyn LanguagePlugin {
    Box::into_raw(Box::new(MyLangPlugin))
}
```

**Build Configuration (`Cargo.toml`):**
```toml
[package]
name = "mylang-plugin"
version = "1.0.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]  # Required for dynamic loading

[dependencies]
arkhe-polyglot = { path = "../parser-core" }
```

**Installation:**
```bash
# Build plugin
cargo build --release

# Install to ARKHE plugin directory
cp target/release/libmylang_plugin.so ~/.arkhe/plugins/

# Verify installation
arkhe-polyglot plugins list
```

### 2. Epigenetic Operator Plugins
Add new quantum operators for epigenetic regulation.

**Interface (`EpigeneticOperator` trait):**
```rust
pub trait EpigeneticOperator: Send + Sync {
    fn name(&self) -> &str;
    fn apply(&self, state: &DensityMatrix, context: &OperatorContext)
        -> Result<DensityMatrix, OperatorError>;
    fn parameters(&self) -> Vec<ParameterSpec>;
    fn verify(&self) -> Result<(), OperatorError>;
}
```

**Example: Acetylation Operator**
```rust
pub struct AcetylationOperator {
    strength: f64,  // 0.0 to 1.0
    target_residues: Vec<String>,  // e.g., ["H3K9", "H3K27"]
}

impl EpigeneticOperator for AcetylationOperator {
    fn apply(&self, state: &DensityMatrix, context: &OperatorContext)
        -> Result<DensityMatrix, OperatorError>
    {
        // Implement acetylation as quantum rotation
        let theta = self.strength * std::f64::consts::PI / 4.0;
        let rotation = Matrix2::new(
            Complex::new(theta.cos(), 0.0),
            Complex::new(0.0, -theta.sin()),
            Complex::new(0.0, theta.sin()),
            Complex::new(theta.cos(), 0.0),
        );
        Ok(rotation * state * rotation.adjoint())
    }
    // ... other methods
}
```

### 3. Analysis Plugin
Add custom semantic analysis or visualization modules.

**Example: Complexity Analyzer**
```python
# complexity_plugin.py
from arkhe.plugins import AnalysisPlugin

class ComplexityAnalyzer(AnalysisPlugin):
    def name(self) -> str: return "complexity"

    def analyze(self, uast: UAST) -> AnalysisReport:
        # Compute cyclomatic complexity, nesting depth, etc.
        report = AnalysisReport(
            metrics={
                "cyclomatic": compute_cyclomatic(uast),
                "nesting": compute_max_nesting(uast),
                "function_count": count_functions(uast),
            },
            score=compute_complexity_score(uast),
        )
        return report
```

## Security Model
Plugins run in sandboxed environments:
- **Hermit**: No I/O, pure computation only
- **Pure**: Math/logic operations, no external state
- **Standard**: Limited I/O (stdin/stdout only)

Specify security profile in `plugin.toml`:
```toml
[security]
level = "Standard"
max_memory_mb = 128
max_execution_time_ms = 5000
blocked_syscalls = ["execve", "fork", "socket"]
```

## Testing Plugins
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mylang_tokenization() {
        let plugin = MyLangPlugin;
        let tokens = plugin.tokenize("let x = 42").unwrap();
        assert!(tokens.contains(&Token::Keyword("let")));
    }
}
```

## Publishing Plugins
1. Create repository with `plugin.toml` metadata
2. Add semantic versioning tags
3. Submit to ARKHE Registry:
```bash
arkhe registry publish ./mylang-plugin --name mylang --version 1.0.0
```

## Troubleshooting
| Issue | Solution |
|-------|----------|
| Plugin not loading | Check `.so`/`.dll` extension and ABI compatibility |
| Verification failed | Ensure `verify()` method returns `Ok(())` |
| Sandbox violation | Review `blocked_syscalls` in security profile |
| Memory limit exceeded | Reduce `max_memory_mb` or optimize plugin logic |

## Resources
- [Plugin API Reference](./api.md)
- [Security Policy Guide](./security.md)
- [Example Plugins Repository](https://github.com/arkhe-os/plugin-examples)