with open(".github/workflows/arkhe-ma-s2-check.yml", "r") as f:
    content = f.read()

bad_block = """        # Upload como artifact
        upload-artifact:
          uses: actions/upload-artifact@v4
          with:
            name: ma-s2-compliance-report
            path: MA_S2_Compliance_Report.md"""

good_block = """    - name: Upload Compliance Report Artifact
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: ma-s2-compliance-report
        path: MA_S2_Compliance_Report.md"""

new_content = content.replace(bad_block, good_block)

with open(".github/workflows/arkhe-ma-s2-check.yml", "w") as f:
    f.write(new_content)
