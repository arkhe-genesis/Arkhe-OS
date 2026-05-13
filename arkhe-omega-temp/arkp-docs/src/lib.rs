
use arkp_core::manifest::PackageManifest;

pub fn generate_docs(manifest: &PackageManifest, sources: &[(&str, &str)]) -> String {
    let mut md = format!("# {} v{}\n\n", manifest.package.name, manifest.package.version);
    md.push_str("## Modules\n\n");
    for (path, content) in sources {
        md.push_str(&format!("### `{}`\n", path));
        let docs: Vec<&str> = content.lines()
            .filter(|l| l.starts_with("///") && !l.starts_with("/// "))
            .map(|l| l.trim_start_matches("///"))
            .collect();
        if !docs.is_empty() {
            md.push_str(&docs.join("\n"));
            md.push('\n');
        }
    }
    md
}
