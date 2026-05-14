#!/bin/bash
# Prepare ARKHE repository for Zenodo/GitHub release

set -e
echo "📦 Preparing ARKHE Ω-TEMP v6.7.0 for Zenodo submission..."

# 1. Generate version tag
VERSION="v6.7.0"
echo "🏷️  Tagging release: $VERSION"
git tag -a "$VERSION" -m "ARKHE Ω-TEMP v6.7.0: Documentation & Publication Release"

# 2. Validate manuscript
echo "📄 Validating Paper 91 LaTeX..."
cd paper91
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
bibtex main.aux > /dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
if [ -f main.pdf ]; then
    echo "✅ Paper 91 PDF generated: main.pdf"
else
    echo "❌ Failed to generate Paper 91 PDF"
    exit 1
fi
cd ..

# 3. Test tutorials
echo "🎓 Testing interactive tutorials..."
if command -v jupyter &> /dev/null; then
    jupyter nbconvert --to notebook --execute tutorials/qnc_for_biologists.ipynb --output /dev/null
    echo "✅ Tutorial executed successfully"
else
    echo "⚠️  Jupyter not found; skipping tutorial execution test"
fi

# 4. Validate plugin interface
echo "🔌 Validating plugin interface..."
cargo test --manifest-path arkhe-polyglot-parser/parser-core/Cargo.toml --lib plugins::interface --quiet
echo "✅ Plugin interface tests passed"

# 5. Generate checksums
echo "🔐 Generating SHA3-256 checksums..."
find . -type f \( -name "*.py" -o -name "*.rs" -o -name "*.tex" -o -name "*.md" \) \
    -not -path "./.git/*" -not -path "./target/*" \
    -exec sha3sum {} \; | sort > checksums.sha3

# 6. Create release archive
echo "📦 Creating release archive..."
ARCHIVE="arkhe-omega-temp-${VERSION}.tar.gz"
tar -czf "$ARCHIVE" --exclude="$ARCHIVE" \
    --exclude='.git' \
    --exclude='target' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    .

# 7. Print submission instructions
echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ ARKHE Ω-TEMP v6.7.0 ready for submission"
echo "═══════════════════════════════════════════════════"
echo ""
echo "📄 Paper 91: paper91/main.pdf"
echo "📦 Archive: $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"
echo "🔐 Checksums: checksums.sha3"
echo ""
echo "🚀 Next steps:"
echo "  1. Push tag to GitHub:"
echo "     git push origin $VERSION"
echo ""
echo "  2. Upload to Zenodo:"
echo "     - Go to https://zenodo.org/deposit"
echo "     - Upload: $ARCHIVE"
echo "     - Fill metadata from .zenodo.json"
echo "     - Submit for DOI assignment"
echo ""
echo "  3. Update GitHub release notes with:"
echo "     - Link to Paper 91 preprint"
echo "     - Tutorial links"
echo "     - Plugin registry URL"
echo ""
echo "🔗 Zenodo DOI will be: 10.5281/zenodo.XXXXXXX"
echo "   (Replace XXXXXXX with assigned DOI after submission)"
echo ""