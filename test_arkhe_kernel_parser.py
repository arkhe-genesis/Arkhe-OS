import pytest
from unittest.mock import patch, MagicMock
from arkhe_kernel_parser import (
    ArkheKernelMemoryManager,
    ArkheKernelInterruptController,
    ArkheKernelBusV3Interface,
    ArkheKernelSyscallInterface,
    ArkheKernelParserModule
)
import json

@pytest.fixture
def parser_module():
    with patch('arkhe_cobol_parse.ArkheCobolParser.parse') as mock_parse:
        mock_parse.return_value = {"program_id": "TESTPROG", "children": []}
        yield ArkheKernelParserModule()

def test_k01_kernel_parse_basic_ok(parser_module):
    source = "IDENTIFICATION DIVISION.\nPROGRAM-ID. TESTPROG.\n"
    res = parser_module.kernel_parse(source)
    assert res is not None
    assert res["ast"]["program_id"] == "TESTPROG"
    assert parser_module.kernel_phi_c == 1.0
    assert res["pages_allocated"] > 0

def test_k02_kernel_parse_cics_ok(parser_module):
    source = "EXEC CICS READ END-EXEC. EXEC CICS WRITE END-EXEC."
    res = parser_module.kernel_parse(source)
    assert len(res["cics"]) == 2
    stats = parser_module.interrupt_controller.get_interrupt_stats()
    assert stats["raised"] == 2
    assert stats["dispatched"] == 2

def test_k03_kernel_parse_ims_ok(parser_module):
    source = "CALL 'CBLTDLI'. CALL 'CBLTDLI'."
    res = parser_module.kernel_parse(source)
    assert len(res["ims"]) == 2

def test_k04_kernel_parse_db2_ok(parser_module):
    source = "EXEC SQL SELECT * FROM EMP END-EXEC."
    res = parser_module.kernel_parse(source)
    assert len(res["db2"]) == 1

def test_k05_kernel_parse_insecure_ok(parser_module):
    source = "ALTER X TO Y. GO TO Z."
    res = parser_module.kernel_parse(source)
    assert len(res["violations"]) == 2

def test_k06_syscall_phi_c_calc_ok(parser_module):
    source = "IDENTIFICATION DIVISION."
    phi_c = parser_module.syscall_interface.execute("COBOL_PHI_C_CALC", "RING3_USER", source=source)
    assert phi_c == 1.0
    assert parser_module.kernel_phi_c == 1.0

def test_k07_ring3_syscall_denied(parser_module):
    with pytest.raises(PermissionError) as excinfo:
        parser_module.syscall_interface.execute("COBOL_PARSE", "RING3_USER", source="")
    assert "RING3 cannot invoke COBOL_PARSE without escalation" in str(excinfo.value)

def test_k08_bus_v3_message_consumed(parser_module):
    parser_module.bus.subscribe("cics_transactions", 1)
    parser_module.bus.publish("cics_transactions", "MSG")
    msg = parser_module.bus.consume("cics_transactions", 1)
    assert msg == "MSG"
    stats = parser_module.get_kernel_stats()
    assert stats["substrate"] == "212-K"

def test_k09_large_cobol_parsed(parser_module):
    source = "A" * 5000
    res = parser_module.kernel_parse(source)
    assert res["pages_allocated"] >= 2

def test_k10_kernel_stats(parser_module):
    stats = parser_module.get_kernel_stats()
    assert stats["substrate"] == "212-K"
    assert stats["kernel_phi_c"] == 1.0
    assert "uptime" in stats
    assert "memory" in stats
    assert "interrupts" in stats
    assert "syscalls" in stats
    assert "bus" in stats

def test_k11_complex_parse_ok(parser_module):
    source = "EXEC CICS R END-EXEC EXEC CICS W END-EXEC CALL 'CBLTDLI'. EXEC SQL S END-EXEC"
    res = parser_module.kernel_parse(source)
    assert len(res["cics"]) == 2
    assert len(res["ims"]) == 1
    assert len(res["db2"]) == 1
    assert len(res["tokens"]) == 2
    stats = parser_module.bus.get_bus_stats()
    assert stats["published"] >= 6

def test_k12_memory_freed(parser_module):
    parser_module.memory_manager.allocate_pages(4096)
    assert parser_module.memory_manager.allocated_pages == 1
    parser_module.memory_manager.free_pages(1)
    assert parser_module.memory_manager.allocated_pages == 0

def test_k13_ast_export_ok(parser_module):
    ast = parser_module.syscall_interface.execute("COBOL_AST_EXPORT", "RING3_USER", source="")
    assert ast["program_id"] == "TESTPROG"

def test_k14_consumer_got_message(parser_module):
    parser_module.bus.subscribe("cics_transactions", 3001)
    parser_module.bus.subscribe("cics_transactions", 3002)
    parser_module.bus.publish("cics_transactions", "M1")
    parser_module.bus.publish("cics_transactions", "M2")
    assert parser_module.bus.consume("cics_transactions", 3001) == "M1"
    assert parser_module.bus.consume("cics_transactions", 3002) == "M2"

def test_k15_kernel_phi_c_degraded(parser_module):
    source = "ALTER X TO Y."
    parser_module.kernel_parse(source)
    assert parser_module.kernel_phi_c < 1.0

def test_k16_extract_cics_syscall_ok(parser_module):
    source = "EXEC CICS READ END-EXEC. EXEC CICS WRITE END-EXEC."
    res = parser_module.syscall_interface.execute("COBOL_EXTRACT_CICS", "RING0_KERNEL", source=source)
    assert len(res) == 2

def test_k17_extract_ims_syscall_ok(parser_module):
    source = "CALL 'CBLTDLI'. CALL 'CBLTDLI'."
    res = parser_module.syscall_interface.execute("COBOL_EXTRACT_IMS", "RING0_KERNEL", source=source)
    assert len(res) == 2

def test_k18_extract_db2_syscall_ok(parser_module):
    source = "EXEC SQL SELECT * FROM EMP END-EXEC."
    res = parser_module.syscall_interface.execute("COBOL_EXTRACT_DB2", "RING0_KERNEL", source=source)
    assert len(res) == 1

def test_k19_fragmentation_tracked(parser_module):
    parser_module.memory_manager.allocate_pages(8192)
    stats = parser_module.memory_manager.get_page_fault_stats()
    assert stats["fragmentation"] > 0

def test_k20_interrupts_handled(parser_module):
    assert len(parser_module.interrupt_controller.handlers) == 4
    parser_module.interrupt_controller.raise_interrupt("CICS_TXN", "DUMMY")
    parser_module.interrupt_controller.dispatch_interrupts()
    stats = parser_module.interrupt_controller.get_interrupt_stats()
    assert stats["dispatched"] == 1
