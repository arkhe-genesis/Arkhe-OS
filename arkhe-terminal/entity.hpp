#ifndef ENTITY_HPP
#define ENTITY_HPP

#include <string>

enum class MonsterType {
    NONE,
    STONE_WORM,
    SHADOW_LEAK,
    DOPPELGANGER,
    VOID_SWARM
};

class Entity {
public:
    int x, y;
    char symbol;
    std::string name;
    MonsterType monsterType;
    bool isPlayer;
    bool blocksMovement;

    Entity(int x, int y, char sym, const std::string& n, bool player = false, bool block = true);
    virtual ~Entity() = default;
};

class Monster : public Entity {
public:
    Monster(int x, int y, MonsterType type);
    std::string getDescription() const;
};

class Player : public Entity {
public:
    Player(int x, int y);
};

#endif
