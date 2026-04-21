#include "arkhe/mind/monster.hpp"
#include <sstream>
#include <iomanip>
#include <cmath>
#include <algorithm>

namespace arkhe::mind {

bool Intention::should_execute() const {
    double noise = static_cast<double>(rand()) / RAND_MAX * 0.1;
    return urgency > (hesitation + noise);
}

MonsterMind::MonsterMind(std::string monster_id) : id(std::move(monster_id)) {
    brain.cell.homeostasis[4] = personality.curiosity; // curiosity
}

MonsterMind::ActionResult MonsterMind::think(
    const std::map<std::string, double>& sensory_input, double dt) {

    age_ticks += dt;

    // 1. PERCEPÇÃO
    auto perception = perceive(sensory_input);

    // 2. COGITAÇÃO (CliffordBiocomputer)
    auto [action_id, state] = brain.think(perception);

    // 3. MEMÓRIA
    MemoryNode mem;
    mem.timestamp = age_ticks;
    mem.emotional_tag = state;
    mem.salience = core::Clifford4D::norm(state);
    if(memories.size() > 200) memories.pop_front();
    memories.push_back(mem);

    // 4. HOMEOSTASE
    std::array<double, 8> actions{};
    brain.cell.update(dt, actions);

    // 5. INTENÇÕES
    generate_intentions(sensory_input);
    auto* chosen = decide();

    // 6. RESULTADO
    ActionResult result;
    if(!chosen) {
        result.action = "idle";
        result.target = "none";
        result.mental_note = "Hesitação geométrica: nenhuma intenção superou o limiar";
        result.hesitated = true;
    } else {
        result.action = chosen->action_type;
        result.target = chosen->target_id;
        result.mental_note = "Intenção " + chosen->action_type + " (urgência="
                           + std::to_string(chosen->urgency).substr(0,4) + ")";
        result.hesitated = false;
    }

    return result;
}

std::vector<double> MonsterMind::perceive(const std::map<std::string, double>& input) {
    std::vector<double> p(32, 0.0);
    p[0] = input.count("distance_to_prey") ? input.at("distance_to_prey") / 100.0 : 1.0;
    p[1] = input.count("distance_to_threat") ? input.at("distance_to_threat") / 100.0 : 1.0;
    p[2] = input.count("health") ? input.at("health") / 100.0 : 1.0;
    p[3] = input.count("time_of_day") ? input.at("time_of_day") / 24.0 : 0.5;
    p[4] = input.count("noise_level") ? input.at("noise_level") : 0.0;
    p[5] = input.count("visible_agents") ? input.at("visible_agents") / 10.0 : 0.0;
    p[6] = input.count("is_injured") ? input.at("is_injured") : 0.0;
    p[7] = input.count("can_see_prey") ? input.at("can_see_prey") : 0.0;
    return p;
}

void MonsterMind::generate_intentions(const std::map<std::string, double>& input) {
    intentions.clear();
    auto& h = brain.cell.homeostasis;

    // FOME
    if(h[0] > 0.6) {
        Intention i;
        i.target_id = "nearest_prey";
        i.action_type = "hunt";
        i.urgency = h[0] * (1.0 + h[3]); // rage aumenta urgência
        intentions.push_back(i);
    }
    // MEDO
    if(h[2] > 0.5) {
        Intention i;
        i.target_id = "threat_source";
        i.action_type = "flee";
        i.urgency = h[2] * 1.2;
        intentions.push_back(i);
    }
    // FADIGA
    if(h[1] > 0.7 || h[7] < 0.2) {
        Intention i;
        i.target_id = "safe_location";
        i.action_type = "rest";
        i.urgency = std::max(h[1], 1.0 - h[7]);
        intentions.push_back(i);
    }

    // Teoria da Mente
    int visible = static_cast<int>(input.count("visible_agents") ? input.at("visible_agents") : 0);
    for(int v=0; v<visible; v++) {
        std::string aid = "agent_" + std::to_string(v);
        if(!theory_of_mind.count(aid)) theory_of_mind[aid] = std::array<double,8>{};
        theory_of_mind[aid][0] = 0.8 * theory_of_mind[aid][0] + 0.2 * 0.3; // simula agressividade
    }

    // Hesitação baseada em ToM
    for(auto& intent : intentions) {
        if(theory_of_mind.count(intent.target_id)) {
            intent.hesitation = theory_of_mind[intent.target_id][0] * 0.5;
        }
    }

    std::sort(intentions.begin(), intentions.end(),
              [](const auto& a, const auto& b){ return a.urgency > b.urgency; });
}

Intention* MonsterMind::decide() {
    for(auto& intent : intentions) {
        if(intent.should_execute()) return &intent;
    }
    return nullptr;
}

std::string MonsterMind::psychological_profile_json() const {
    std::stringstream ss;
    ss << "{";
    ss << "\"id\":\"" << id << "\",";
    ss << "\"age_ticks\":" << age_ticks << ",";
    ss << "\"homeostasis\":{";
    ss << "\"hunger\":" << brain.cell.homeostasis[0] << ",";
    ss << "\"fatigue\":" << brain.cell.homeostasis[1] << ",";
    ss << "\"fear\":" << brain.cell.homeostasis[2] << ",";
    ss << "\"rage\":" << brain.cell.homeostasis[3] << ",";
    ss << "\"energy\":" << brain.cell.homeostasis[7];
    ss << "},";
    ss << "\"memory_count\":" << memories.size() << ",";
    ss << "\"intentions\":" << intentions.size() << ",";
    // Use the member function directly or a simplified logic for JSON
    ss << "\"hesitating\":" << (intentions.empty() ? "true" : "false");
    ss << "}";
    return ss.str();
}

} // namespace arkhe::mind
