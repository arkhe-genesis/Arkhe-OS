#pragma once
#include "arkhe/core/biocomputer.hpp"
#include <string>
#include <deque>
#include <map>

namespace arkhe::mind {

// ═══════════════════════════════════════════════════════════════════════════════
// INTENTION — Vetor de Ação no Espaço de Clifford
// ═══════════════════════════════════════════════════════════════════════════════
struct Intention {
    std::string target_id;
    std::string action_type; // hunt, flee, socialize, rest, idle
    double urgency = 0.0;
    double hesitation = 0.0;
    std::array<double, 8> expected_outcome{};

    bool should_execute() const;
};

// ═══════════════════════════════════════════════════════════════════════════════
// EPISODIC MEMORY — Hippocampus Digital
// ═══════════════════════════════════════════════════════════════════════════════
struct MemoryNode {
    double timestamp;
    std::string content;
    core::Clifford4D::Multivector emotional_tag;
    double salience = 0.5;
};

// ═══════════════════════════════════════════════════════════════════════════════
// MONSTER MIND — NPC Vivo
// ═══════════════════════════════════════════════════════════════════════════════
class MonsterMind {
public:
    std::string id;
    core::CliffordBiocomputer brain;

    struct Personality {
        double aggressiveness = 0.5;
        double sociability = 0.5;
        double curiosity = 0.5;
        double neuroticism = 0.5;
    } personality;

    std::deque<MemoryNode> memories;
    std::vector<Intention> intentions;
    std::map<std::string, std::array<double, 8>> theory_of_mind;

    double age_ticks = 0.0;
    bool alive = true;

    explicit MonsterMind(std::string monster_id);

    // Ciclo cognitivo completo
    struct ActionResult {
        std::string action;
        std::string target;
        std::string mental_note;
        bool hesitated;
    };

    ActionResult think(const std::map<std::string, double>& sensory_input, double dt);

    // Perfil psicológico para debug/MERKABAH
    std::string psychological_profile_json() const;

private:
    std::vector<double> perceive(const std::map<std::string, double>& input);
    void generate_intentions(const std::map<std::string, double>& input);
    Intention* decide();
};

} // namespace arkhe::mind
