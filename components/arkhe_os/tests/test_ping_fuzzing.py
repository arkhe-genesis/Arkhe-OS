import pytest
from arkhe_os.parser.frontends.ping_frontend import PingParser

FAULTY_OUTPUTS = [
    "",                                                       # vazio
    "PING 8.8.8.8: 56 data bytes\n",                        # sem resposta
    "64 bytes from 8.8.8.8: icmp_seq=0 ttl=118 time=?\n",   # campo corrompido
    "time=12.3 ms\ntime=15.7 ms\ntime=error ms\n",           # erro no terceiro RTT
    "100% packet loss\n",                                    # perda total
    "\x00\x01\x02\x03\n",                                     # binário inválido
]

class TestPingFuzzing:
    """Valida resiliência do parser contra outputs malformados."""

    @pytest.mark.parametrize("faulty_output", FAULTY_OUTPUTS)
    def test_parser_survives_faulty_output(self, faulty_output):
        """O parser não deve lançar exceção para nenhum output malformado."""
        parser = PingParser()
        # Sobrescreve o subprocesso para retornar o output injetado
        parser._run_ping = lambda target, count: faulty_output
        result = parser.parse("8.8.8.8", count=3)
        # Para output vazio ou perda total, coerência deve ser 0.0
        assert 0.0 <= result.coherence <= 1.0
        assert result.loss_rate >= 0.0
