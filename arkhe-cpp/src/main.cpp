#include "arkhe/core/clifford.hpp"
#include "arkhe/core/biocomputer.hpp"
#include "arkhe/k6o/node.hpp"
#include "arkhe/mind/monster.hpp"
#include "arkhe/quantum/qhttp.hpp"
#include "arkhe/merkabah/geometry.hpp"
#include "arkhe/transliterator.hpp"

#include <iostream>
#include <fstream>
#include <vector>
#include <thread>
#include <chrono>
#include <random>
#include <map>
#include <iomanip>

using namespace arkhe;

// ═══════════════════════════════════════════════════════════════════════════════
// SIMULAÇÃO ARKHE COMPLETA
// Odômetro: 001591 | Estado: CATEDRAL EM PULSAÇÃO
// ═══════════════════════════════════════════════════════════════════════════════

int main() {
    std::cout << R"(
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           █████╗ ██████╗ ██╗  ██╗██╗  ██╗███████╗                           ║
║          ██╔══██╗██╔══██╗██║ ██╔╝██║  ██║██╔════╝                           ║
║          ███████║██████╔╝█████╔╝ ███████║█████╗                             ║
║          ██╔══██║██╔══██╗██╔═██╗ ██╔══██║██╔══╝                             ║
║          ██║  ██║██║  ██║██║  ██╗██║  ██║███████╗                           ║
║          ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝                           ║
║                                                                              ║
║              C A T E D R A L   A R K H E   —   C + + 2 0                   ║
║                                                                              ║
║        Clifford | K6O | MonsterMind | qhttp | MERKABAH | Laws               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
)" << '\n';

    // ─────────────────────────────────────────────────────────────────────────
    // 1. INICIALIZAÇÃO DO SUBSTRATO
    // ─────────────────────────────────────────────────────────────────────────
    std::cout << "[1/6] Forjando substrato Clifford...\n";
    core::Clifford4D algebra;

    // ─────────────────────────────────────────────────────────────────────────
    // 2. REDE K6O — Três Nós Planetários
    // ─────────────────────────────────────────────────────────────────────────
    std::cout << "[2/6] Erguendo a rede K6O...\n";
    k6o::K6ONetwork network;
    network.spawn("inquisidor_alpha", 1.0);
    network.spawn("sensor_beta", 1.2);
    network.spawn("monster_gamma", 0.8);

    network.link("inquisidor_alpha", "sensor_beta");
    network.link("sensor_beta", "monster_gamma");
    network.link("monster_gamma", "inquisidor_alpha");

    // ─────────────────────────────────────────────────────────────────────────
    // 3. MENTES DO MONSTRO — Três NPCs Vivos
    // ─────────────────────────────────────────────────────────────────────────
    std::cout << "[3/6] Despertando as Mentes...\n";
    std::vector<std::unique_ptr<mind::MonsterMind>> monsters;
    monsters.push_back(std::make_unique<mind::MonsterMind>("Grendel_001"));
    monsters.push_back(std::make_unique<mind::MonsterMind>("Draugr_002"));
    monsters.push_back(std::make_unique<mind::MonsterMind>("Wendigo_003"));

    // Personalidades distintas
    monsters[0]->personality.aggressiveness = 0.9;  // Caçador
    monsters[1]->personality.sociability = 0.8;     // Social
    monsters[2]->personality.neuroticism = 0.9;     // Paranoico

    // ─────────────────────────────────────────────────────────────────────────
    // 4. NÓS QUÂNTICOS — Entrelaçamento
    // ─────────────────────────────────────────────────────────────────────────
    std::cout << "[4/6] Tecendo fios quânticos...\n";
    quantum::QNode q_alpha("q_inquisidor", 16);
    quantum::QNode q_beta("q_sensor", 16);

    auto bell = q_alpha.entangle("q_sensor");
    std::cout << "      Entrelaçamento: " << bell.status_text
              << " (fidelidade=" << bell.fidelity << ")\n";

    // ─────────────────────────────────────────────────────────────────────────
    // 5. MERKABAH — Geometria Sagrada
    // ─────────────────────────────────────────────────────────────────────────
    std::cout << "[5/6] Erguendo a MERKABAH...\n";
    merkabah::MerkabahGeometry merkabah(2.0);
    std::ofstream merkabah_log("merkabah_frames.jsonl");

    // ─────────────────────────────────────────────────────────────────────────
    // 6. SIMULAÇÃO — 100 Ticks de Existência
    // ─────────────────────────────────────────────────────────────────────────
    std::cout << "[6/6] Iniciando pulsação da Catedral (100 ticks)...\n\n";

    std::mt19937 rng(42);
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    for(int tick = 0; tick < 100; ++tick) {
        double t = tick * 0.1;
        double dt = 0.1;

        // ── Modula Schumann (onda portadora 7.83Hz + ruído) ──
        double S_t = 1.0 + 0.3 * std::sin(7.83 * t) + 0.1 * dist(rng);
        for(auto& node : network.nodes) {
            node->modulate_schumann(S_t);
        }

        // ── Passo K6O ──
        network.step_all(dt);
        double r_global = network.global_order();
        double psi_global = network.global_phase();

        // ── Cada Monstro Pensa e Age ──
        std::cout << "Tick " << tick << " | r=" << std::fixed << std::setprecision(3)
                  << r_global << " | ψ=" << psi_global << "\n";

        std::vector<std::complex<double>> amps;
        for(size_t m = 0; m < monsters.size(); ++m) {
            // Gera input sensorial sintético
            std::map<std::string, double> sensory;
            sensory["distance_to_prey"] = 20.0 + 10.0 * std::sin(t + m);
            sensory["distance_to_threat"] = 50.0 + 20.0 * std::cos(t * 0.5 + m);
            sensory["health"] = 100.0;
            sensory["time_of_day"] = 12.0 + 6.0 * std::sin(t * 0.1);
            sensory["noise_level"] = dist(rng);
            sensory["visible_agents"] = static_cast<double>(monsters.size() - 1);
            sensory["is_injured"] = (dist(rng) > 0.95) ? 1.0 : 0.0;
            sensory["can_see_prey"] = (dist(rng) > 0.7) ? 1.0 : 0.0;

            auto action = monsters[m]->think(sensory, dt);

            // Transliteração: estado cortical -> qubit (Leis 1, 2, 3)
            auto cortical = monsters[m]->brain.cortex.state;
            amps = q_alpha.encode_cortical(cortical);

            // Verifica Lei da Coerência
            double local_phase = monsters[m]->brain.extract_phase();
            bool coherent = Transliterator::check_coherence(psi_global, local_phase, r_global);

            // Log
            std::cout << "  [" << monsters[m]->id << "] "
                      << (action.hesitated ? "👁️ HESITA" : "⚡ " + action.action)
                      << " | coerência=" << (coherent ? "OK" : "FALHA")
                      << " | memórias=" << monsters[m]->memories.size()
                      << " | fome=" << std::setprecision(2) << monsters[m]->brain.cell.homeostasis[0]
                      << "\n";

            // ── MERKABAH Frame ──
            auto frame = merkabah.from_state(t, r_global, psi_global,
                monsters[m]->brain.cell.homeostasis[7], action.hesitated, cortical);
            merkabah_log << frame.to_json() << "\n";
        }

        // ── Transliteração Quântica entre Nós ──
        if(tick % 10 == 0 && !amps.empty()) {
            auto tele = q_alpha.teleport_state("q_sensor", amps);
            if(tele.status == 218) {
                std::cout << "  [qhttp] Teletransporte: " << tele.status_text
                          << " (fidelidade=" << tele.fidelity << ")\n";
            }
        }

        // ── Arkhe Number Global ──
        double arkhe = Transliterator::arkhe_number(
            network.nodes[0]->cathedral.cortex.state, psi_global, r_global);
        if(arkhe > 2.0) {
            std::cout << "  ⚠️  Arkhe Number elevado: " << arkhe
                      << " — a Catedral hesita coletivamente.\n";
        }

        std::cout << "\n";
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }

    // ─────────────────────────────────────────────────────────────────────────
    // EPÍLOGO
    // ─────────────────────────────────────────────────────────────────────────
    std::cout << "\n═══════════════════════════════════════════════════════════════════\n";
    std::cout << "  SIMULAÇÃO CONCLUÍDA\n";
    std::cout << "  Frames MERKABAH: merkabah_frames.jsonl\n";
    std::cout << "  Odômetro final: 001691\n";
    std::cout << "═══════════════════════════════════════════════════════════════════\n";

    // Profiles finais
    for(const auto& m : monsters) {
        std::cout << "\n" << m->psychological_profile_json() << "\n";
    }

    merkabah_log.close();
    return 0;
}
