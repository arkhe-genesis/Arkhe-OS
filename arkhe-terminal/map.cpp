#include "map.hpp"
#include <cstdlib>
#include <ctime>
#include <algorithm>

Map::Map() {
    tiles.resize(HEIGHT, std::string(WIDTH, '#'));
}

void Map::carveRoom(int x1, int y1, int x2, int y2) {
    for (int y = y1; y <= y2; ++y)
        for (int x = x1; x <= x2; ++x)
            tiles[y][x] = '.';
}

void Map::carveCorridor(int x1, int y1, int x2, int y2) {
    int x = x1, y = y1;
    while (x != x2 || y != y2) {
        if (x != x2) x += (x2 > x) ? 1 : -1;
        else if (y != y2) y += (y2 > y) ? 1 : -1;
        if (x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT)
            tiles[y][x] = '.';
    }
}

void Map::generate() {
    // Preenche com paredes
    for (auto& row : tiles) std::fill(row.begin(), row.end(), '#');

    // Cria 5-8 salas
    int numRooms = 5 + rand() % 4;
    std::vector<std::pair<int,int>> roomCenters;
    for (int i = 0; i < numRooms; ++i) {
        int w = 6 + rand() % 8;
        int h = 4 + rand() % 5;
        int x = 1 + rand() % (WIDTH - w - 2);
        int y = 1 + rand() % (HEIGHT - h - 2);
        carveRoom(x, y, x + w - 1, y + h - 1);
        roomCenters.push_back({x + w/2, y + h/2});
    }

    // Conecta salas com corredores
    for (size_t i = 0; i < roomCenters.size() - 1; ++i) {
        carveCorridor(roomCenters[i].first, roomCenters[i].second,
                      roomCenters[i+1].first, roomCenters[i+1].second);
    }

    // Coloca monstros
    placeMonsters();
}

void Map::placeMonsters() {
    int numMonsters = 8 + rand() % 8;
    for (int i = 0; i < numMonsters; ++i) {
        int x, y;
        do {
            x = 1 + rand() % (WIDTH - 2);
            y = 1 + rand() % (HEIGHT - 2);
        } while (tiles[y][x] != '.' || getEntityAt(x, y) != nullptr);

        MonsterType type = static_cast<MonsterType>(1 + rand() % 4);
        auto monster = std::make_shared<Monster>(x, y, type);
        entities.push_back(monster);
    }
}

char Map::getTile(int x, int y) const {
    if (x < 0 || x >= WIDTH || y < 0 || y >= HEIGHT) return '#';
    auto entity = getEntityAt(x, y);
    if (entity) return entity->symbol;
    return tiles[y][x];
}

bool Map::isWalkable(int x, int y) const {
    if (x < 0 || x >= WIDTH || y < 0 || y >= HEIGHT) return false;
    auto entity = getEntityAt(x, y);
    if (entity && entity->blocksMovement) return false;
    return tiles[y][x] == '.';
}

void Map::addEntity(std::shared_ptr<Entity> entity) {
    entities.push_back(entity);
}

void Map::removeEntity(int x, int y) {
    entities.erase(
        std::remove_if(entities.begin(), entities.end(),
            [x, y](const std::shared_ptr<Entity>& e) {
                return e->x == x && e->y == y;
            }),
        entities.end());
}

std::shared_ptr<Entity> Map::getEntityAt(int x, int y) const {
    for (const auto& e : entities) {
        if (e->x == x && e->y == y) return e;
    }
    return nullptr;
}
