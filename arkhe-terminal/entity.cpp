#include "entity.hpp"

Entity::Entity(int x, int y, char sym, const std::string& n, bool player, bool block)
    : x(x), y(y), symbol(sym), name(n), monsterType(MonsterType::NONE),
      isPlayer(player), blocksMovement(block) {}

Monster::Monster(int x, int y, MonsterType type)
    : Entity(x, y, 'M', "Unknown", false, true) {
    monsterType = type;
    switch (type) {
        case MonsterType::STONE_WORM:
            symbol = 'W'; name = "Verme de Pedra"; break;
        case MonsterType::SHADOW_LEAK:
            symbol = 'S'; name = "Sombra Vazante"; break;
        case MonsterType::DOPPELGANGER:
            symbol = 'D'; name = "Doppelgänger"; break;
        case MonsterType::VOID_SWARM:
            symbol = 'V'; name = "Praga de Gafanhotos"; break;
        default: break;
    }
}

std::string Monster::getDescription() const {
    switch (monsterType) {
        case MonsterType::STONE_WORM:
            return "Rochas retorcidas com veios opacos... Algo range sob a superfície.";
        case MonsterType::SHADOW_LEAK:
            return "Uma névoa púrpura quase invisível. Você sente que está sendo observado.";
        case MonsterType::DOPPELGANGER:
            return "Uma silhueta familiar, mas os olhos... os olhos estão errados.";
        case MonsterType::VOID_SWARM:
            return "Inúmeros fragmentos negros zumbindo. O ar parece pesado.";
        default:
            return "Uma presença inexplicável.";
    }
}

Player::Player(int x, int y) : Entity(x, y, '@', "Você", true, true) {}
