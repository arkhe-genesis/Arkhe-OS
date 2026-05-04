// tb_tau_soc_regression.cpp
// Driver C++ para Verilator do TAU SoC Wrapper
// Inclui: Injeção de Frames, Backpressure Aleatória e Verificação de Interrupção

#include "Vtau_soc_wrapper.h"
#include "verilated.h"
#include "verilated_vcd_c.h"
#include <iostream>
#include <cstdlib>
#include <ctime>

#define VOXEL_DATA_WIDTH 128
#define ROI_WIDTH 64
#define CLK_PERIOD 10 // 100MHz = 10ns

static Vtau_soc_wrapper *dut;
static VerilatedVcdC *tfp;

double sc_time_stamp() { return tfp->time(); }

void tick() {
    dut->clk_100mhz_p = !dut->clk_100mhz_p;
    dut->clk_100mhz_n = !dut->clk_100mhz_n;
    dut->eval();
    tfp->dump(tfp->time());
    tfp->timeInc(CLK_PERIOD/2);

    dut->clk_100mhz_p = !dut->clk_100mhz_p;
    dut->clk_100mhz_n = !dut->clk_100mhz_n;
    dut->eval();
    tfp->dump(tfp->time());
    tfp->timeInc(CLK_PERIOD/2);
}

void reset_dut() {
    dut->rst_n_btn = 0;
    for (int i = 0; i < 20; ++i) tick();
    dut->rst_n_btn = 1;
    for (int i = 0; i < 50; ++i) tick(); // Aguarda PLL lock simulado
    std::cout << "[DRIVER] Reset liberado." << std::endl;
}

void send_voxel(uint16_t x, uint16_t y, uint16_t z,
                uint8_t r, uint8_t g, uint8_t b, uint16_t intensity, bool last) {
    // Monta o pacote de 128 bits: [intensity, b, g, r, z, y, x]
    // Nota: Verilator pode representar sinais largos de forma diferente.
    // Para 128 bits, s_axis_lidar_tdata pode ser um array ou WData.
    // Verificaremos a definição gerada por Verilator se falhar a compilação.

    // Tentativa de atribuição direta para 128 bits (se suportado pelo compilador C++ e Verilator)
    // Se não, precisaremos usar dut->s_axis_lidar_tdata[0], [1], etc.

    // [127:112] intensity
    // [111:104] b
    // [103:96]  g
    // [95:88]   r
    // [87:72]   z
    // [71:56]   y
    // [55:40]   x
    // Restante [39:0] zero ou padding

    // Simplificando a injeção para o testbench se s_axis_lidar_tdata for um array
#if defined(VERILATOR)
    // Verilator v5+ uses VlWide for > 64 bits.
    // s_axis_lidar_tdata is likely WData[4]
    dut->s_axis_lidar_tdata[0] = (uint32_t)y | ((uint32_t)z << 16);
    dut->s_axis_lidar_tdata[1] = (uint32_t)r | ((uint32_t)g << 8) | ((uint32_t)b << 16) | ((uint32_t)(intensity & 0xFF) << 24);
    dut->s_axis_lidar_tdata[2] = (uint32_t)(intensity >> 8);
    dut->s_axis_lidar_tdata[3] = (uint32_t)x;
#else
    uint64_t low  = ((uint64_t)intensity << 48) | ((uint64_t)b << 40) | ((uint64_t)g << 32) | (r << 24) | (z << 8) | (y);
    uint64_t high = x;
    dut->s_axis_lidar_tdata = (((unsigned __int128)high) << 64) | low;
#endif

    dut->s_axis_lidar_tvalid = 1;
    dut->s_axis_lidar_tlast = last ? 1 : 0;

    // Aguarda tready
    int timeout = 1000;
    do {
        tick();
        if (--timeout == 0) {
            std::cerr << "[DRIVER] TIMEOUT aguardando s_axis_lidar_tready" << std::endl;
            break;
        }
    } while (!dut->s_axis_lidar_tready);

    // Handshake concluído
    tick();
    dut->s_axis_lidar_tvalid = 0;
    dut->s_axis_lidar_tlast = 0;
}

void send_test_frame(int num_voxels, bool random_colors = true) {
    std::cout << "[DRIVER] Enviando frame com " << num_voxels << " voxels..." << std::endl;
    for (int i = 0; i < num_voxels; ++i) {
        uint8_t r, g, b;
        if (random_colors && (i % 10 == 0)) {
            r = 0xFF; g = 0x00; b = 0x00; // Vermelho (interessante)
        } else if (random_colors && (i % 7 == 0)) {
            r = 0x00; g = 0xFF; b = 0x00; // Verde (interessante)
        } else {
            r = 0x40; g = 0x40; b = 0x40; // Cinza (não interessante)
        }
        send_voxel(i*10, (i*7)%1024, (i*3)%512, r, g, b, 0xFFFF, (i == num_voxels-1));
    }
}

int main(int argc, char **argv) {
    Verilated::commandArgs(argc, argv);
    srand(time(NULL));

    dut = new Vtau_soc_wrapper;
    tfp = new VerilatedVcdC;
    Verilated::traceEverOn(true);
    dut->trace(tfp, 99);
    tfp->open("tau_soc_regression.vcd");

    // Inicialização de entradas
    dut->rst_n_btn = 1;
    dut->clk_100mhz_p = 0;
    dut->clk_100mhz_n = 1;
    // i_ibmq_correction is 128 bits
    for(int i=0; i<4; i++) dut->i_ibmq_correction[i] = 0;
    dut->i_dac_ready = 1;
    dut->i_cfg_grid_shift = 2;      // 4mm grid
    dut->i_cfg_red_threshold = 0x80;
    dut->i_cfg_green_threshold = 0x80;
    dut->i_cfg_blue_threshold = 0x80;

    // Backpressure aleatório (controlado pelo driver)
    bool backpressure = false;

    std::cout << "========================================" << std::endl;
    std::cout << " TAU SoC Regression Testbench (Verilator)" << std::endl;
    std::cout << "========================================" << std::endl;

    reset_dut();

    // Monitoramento de resultados esperados
    uint32_t last_frame_count = 0;
    uint32_t roi_packet_count = 0;
    bool irq_detected = false;

    // ==================== TESTE 1: Frame Normal ====================
    std::cout << "[TEST 1] Frame único sem backpressure" << std::endl;
    dut->m_axis_roi_tready = 1;
    send_test_frame(100, true);

    // Espera processamento
    for (int i = 0; i < 500; ++i) {
        tick();
        if (dut->o_irq_roi_frame_done) irq_detected = true;
        if (dut->m_axis_roi_tvalid && dut->m_axis_roi_tready) {
            roi_packet_count++;
        }
    }

    if (dut->o_vrp_frame_count > last_frame_count && irq_detected) {
        std::cout << "[TEST 1] PASS: Frame contabilizado e IRQ recebida. ROI packets: "
                  << roi_packet_count << std::endl;
    } else {
        std::cout << "[TEST 1] FAIL: Frame count = " << dut->o_vrp_frame_count
                  << ", IRQ = " << irq_detected << std::endl;
    }
    last_frame_count = dut->o_vrp_frame_count;
    roi_packet_count = 0;
    irq_detected = false;

    // ==================== TESTE 2: Backpressure ====================
    std::cout << "[TEST 2] Frame com backpressure aleatória" << std::endl;
    // Aplicar backpressure durante a injeção e depois
    send_test_frame(100, true);

    for (int i = 0; i < 1000; ++i) {
        if (i % 23 == 0) backpressure = !backpressure;
        dut->m_axis_roi_tready = backpressure ? 0 : 1;
        tick();
        if (dut->o_irq_roi_frame_done) irq_detected = true;
        if (dut->m_axis_roi_tvalid && dut->m_axis_roi_tready) {
            roi_packet_count++;
        }
    }

    // Verifica se não houve perda de integridade
    if (dut->o_vrp_frame_count > last_frame_count && irq_detected) {
        std::cout << "[TEST 2] PASS: Frame processado com backpressure. ROI packets: "
                  << roi_packet_count << std::endl;
    } else {
        std::cout << "[TEST 2] FAIL: Frame count = " << dut->o_vrp_frame_count << std::endl;
    }
    last_frame_count = dut->o_vrp_frame_count;
    irq_detected = false;

    // ==================== TESTE 3: Sobrecarga da FIFO ====================
    std::cout << "[TEST 3] Sobrecarga da FIFO (NoC lento)" << std::endl;
    dut->m_axis_roi_tready = 0; // NoC não está pronto nunca
    send_test_frame(200, true); // Muitos voxels interessantes

    // Aguarda a FIFO encher
    for (int i = 0; i < 300; ++i) {
        tick();
    }

    // Libera o NoC
    dut->m_axis_roi_tready = 1;
    for (int i = 0; i < 1000; ++i) {
        tick();
        if (dut->o_irq_roi_frame_done) irq_detected = true;
    }

    if (dut->o_vrp_frame_count > last_frame_count) {
        std::cout << "[TEST 3] PASS: Frame completado após sobrecarga. IRQ = "
                  << irq_detected << std::endl;
    } else {
        std::cout << "[TEST 3] FAIL: Frame count = " << dut->o_vrp_frame_count << std::endl;
    }

    tfp->close();
    delete dut;
    delete tfp;

    std::cout << "Simulação concluída." << std::endl;
    return 0;
}
