import pytest
import time

class RelayNode:
    def __init__(self, name: str, buffer_tb: float):
        self.name = name
        self.buffer_tb = buffer_tb
        self.stored_data_tb = 0.0
        self.link_active = True

    def receive_data(self, amount_tb: float):
        if self.stored_data_tb + amount_tb > self.buffer_tb:
            raise ValueError(f"{self.name} buffer overflow!")
        self.stored_data_tb += amount_tb

    def transmit_data(self):
        if self.link_active:
            transmitted = self.stored_data_tb
            self.stored_data_tb = 0.0
            return transmitted
        return 0.0

@pytest.mark.physics
def test_store_and_forward_buffer():
    """Valida tolerância de 30 dias de interrupção de enlace com buffer de 10 TB."""
    # Instanciando nós com buffer de 10 TB
    fobos = RelayNode("Fobos", 10.0)
    eml1 = RelayNode("EML1", 10.0)

    # Taxa de dados acumulados por dia: 0.1 Mbps = ~1.08 GB/dia -> ~0.001 TB/dia.
    # Digamos que a telemetria diária comprimida seja 0.1 TB / dia
    daily_data_tb = 0.1

    # Interrupção de 30 dias
    fobos.link_active = False
    eml1.link_active = False

    for _ in range(30):
        fobos.receive_data(daily_data_tb)
        eml1.receive_data(daily_data_tb)

    # Verifica o quanto acumulou
    assert fobos.stored_data_tb == pytest.approx(3.0)
    assert eml1.stored_data_tb == pytest.approx(3.0)
    assert fobos.stored_data_tb <= fobos.buffer_tb
    assert eml1.stored_data_tb <= eml1.buffer_tb

    # Restaurar link
    fobos.link_active = True
    eml1.link_active = True

    fobos.transmit_data()
    eml1.transmit_data()

    assert fobos.stored_data_tb == 0.0
    assert eml1.stored_data_tb == 0.0
