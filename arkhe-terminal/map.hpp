#ifndef MAP_HPP
#define MAP_HPP

#include <vector>
#include <memory>
#include "entity.hpp"

class Map {
public:
    static const int WIDTH = 80;
    static const int HEIGHT = 24;

    Map();
    void generate();
    char getTile(int x, int y) const;
    bool isWalkable(int x, int y) const;
    void addEntity(std::shared_ptr<Entity> entity);
    void removeEntity(int x, int y);
    std::shared_ptr<Entity> getEntityAt(int x, int y) const;
    const std::vector<std::shared_ptr<Entity>>& getEntities() const { return entities; }

private:
    std::vector<std::string> tiles;
    std::vector<std::shared_ptr<Entity>> entities;

    void carveRoom(int x1, int y1, int x2, int y2);
    void carveCorridor(int x1, int y1, int x2, int y2);
    void placeMonsters();
};

#endif
