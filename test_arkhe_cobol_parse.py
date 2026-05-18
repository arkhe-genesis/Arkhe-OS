import pytest
from unittest.mock import patch, mock_open
from arkhe_cobol_parse import ArkheCobolParser, ArkheCobolSecurityRules
import json

def test_cobol_parser_cics():
    sample_cobol = '''
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TESTCICS.
       PROCEDURE DIVISION.
           EXEC CICS
               RECEIVE MAP('TESTMAP')
               MAPSET('TESTSET')
           END-EXEC.
    '''

    mock_stdout = json.dumps({"children": [{"type": "PROGRAM_ID", "value": "TESTCICS"}, {"type": "PROCEDURE_DIVISION", "children": []}]})

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = mock_stdout

        parser = ArkheCobolParser(proleap_jar="dummy.jar")
        ast = parser.parse(sample_cobol)
        assert ast['program_id'] == 'TESTCICS'
        assert len(ast['cics_transactions']) == 1
        assert "RECEIVE MAP" in ast['cics_transactions'][0]

def test_cobol_security_rules():
    rules = ArkheCobolSecurityRules()

    clean_cobol = "DISPLAY 'HELLO'."
    assert len(rules.validate(clean_cobol)) == 0

    alter_cobol = "ALTER PARA-1 TO PROCEED TO PARA-2."
    violations = rules.validate(alter_cobol)
    assert len(violations) == 1
    assert "ALTER" in violations[0]

    goto_cobol = "GO TO PARA-END."
    violations = rules.validate(goto_cobol)
    assert len(violations) == 1
    assert "GO TO" in violations[0]
