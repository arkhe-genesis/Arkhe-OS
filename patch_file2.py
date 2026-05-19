with open("substrato_255.py", "r") as f:
    text = f.read()

# Replace security-scan block
old_sec = """  security-scan:
    needs: build-image
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: arkhe-core-26-arm64
          path: ./arm64
      - name: Run Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: './arm64/*.img'
          format: 'sarif'
          output: 'trivy-results.sarif'
      - name: Upload scan results
        uses: actions/upload-artifact@v4
        with:
          name: security-scan-results
          path: trivy-results.sarif"""

new_sec = """  security-scan:
    needs: build-image
    runs-on: ubuntu-latest
    strategy:
      matrix:
        arch: [arm64, amd64, riscv64]
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: arkhe-core-26-${{ matrix.arch }}
          path: ./${{ matrix.arch }}
      - name: Run Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: './${{ matrix.arch }}/*.img'
          format: 'sarif'
          output: 'trivy-results-${{ matrix.arch }}.sarif'
      - name: Upload scan results
        uses: actions/upload-artifact@v4
        with:
          name: security-scan-results-${{ matrix.arch }}
          path: trivy-results-${{ matrix.arch }}.sarif"""

text = text.replace(old_sec, new_sec)

# Add *.snap to artifact path
old_art = """      - name: Upload image artifact
        uses: actions/upload-artifact@v4
        with:
          name: arkhe-core-26-${{ matrix.arch }}
          path: |
            *.img
            *.model
            *.model.sig
            canonical.seal"""

new_art = """      - name: Upload image artifact
        uses: actions/upload-artifact@v4
        with:
          name: arkhe-core-26-${{ matrix.arch }}
          path: |
            *.img
            *.model
            *.model.sig
            *.snap
            canonical.seal"""

text = text.replace(old_art, new_art)

with open("substrato_255.py", "w") as f:
    f.write(text)
