#include "game.hpp"
#include <iostream>
#include <cstdlib>
#include <algorithm>
#include <ctime>

#ifdef _WIN32
#include <conio.h>
#include <windows.h>
#else
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>
int _getch() {
    struct termios oldt, newt;
    int ch;
    tcgetattr(STDIN_FILENO, &oldt);
    newt = oldt;
    newt.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &newt);
    ch = getchar();
    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
    return ch;
}
#endif

void Game::clearScreen() {
#ifdef _WIN32
    system("cls");
#else
    system("clear");
#endif
}

Game::Game() : running(true) {
    srand(static_cast<unsigned>(time(nullptr)));
    map = std::make_unique<Map>();
    map->generate();

    // Encontra uma posição walkable para o jogador
    int px, py;
    do {
        px = 1 + rand() % (Map::WIDTH - 2);
        py = 1 + rand() % (Map::HEIGHT - 2);
    } while (!map->isWalkable(px, py));
    player = std::make_shared<Player>(px, py);
    map->addEntity(player);

    // Inicializa telemetria (use mock server ou localhost)
    telemetry = std::make_unique<Telemetry>("http://localhost:8080/telemetry");

    addMessage("Você adentra o Véu. A Muralha observa em silêncio.");
    addMessage("Use WASD para mover, 'f' para escanear, 'r' para reportar.");
}

Game::~Game() {}

void Game::addMessage(const std::string& msg) {
    messageLog.push_back(msg);
    if (messageLog.size() > 5) messageLog.erase(messageLog.begin());
}

void Game::render() {
    clearScreen();

    // Desenha o mapa
    for (int y = 0; y < Map::HEIGHT; ++y) {
        for (int x = 0; x < Map::WIDTH; ++x) {
            char tile = map->getTile(x, y);
            if (tile == '@') std::cout << "\033[1;32m@\033[0m";  // jogador verde
            else if (tile == 'W') std::cout << "\033[1;31mW\033[0m";
            else if (tile == 'S') std::cout << "\033[1;35mS\033[0m";
            else if (tile == 'D') std::cout << "\033[1;33mD\033[0m";
            else if (tile == 'V') std::cout << "\033[1;36mV\033[0m";
            else if (tile == '.') std::cout << '.';
            else std::cout << "\033[1;30m#\033[0m";
        }
        std::cout << '\n';
    }

    // Status
    std::cout << "\n[POS: " << player->x << "," << player->y << "] ";
    auto entity = map->getEntityAt(player->x, player->y);
    if (entity && entity != player) {
        auto monster = std::dynamic_pointer_cast<Monster>(entity);
        if (monster) {
            std::cout << "Você está sobre " << monster->name << ".";
        }
    }
    std::cout << "\n";

    // Mensagens
    std::cout << "--- Log de Consciência ---\n";
    for (const auto& msg : messageLog) {
        std::cout << msg << '\n';
    }
    std::cout << "---------------------------\n";
    std::cout << "[WASD] mover  [F]scan  [R]eportar  [Q]uit\n";
}

void Game::movePlayer(int dx, int dy) {
    int nx = player->x + dx;
    int ny = player->y + dy;
    if (map->isWalkable(nx, ny)) {
        map->removeEntity(player->x, player->y);
        player->x = nx;
        player->y = ny;
        map->addEntity(player);

        auto entity = map->getEntityAt(nx, ny);
        if (entity && entity != player) {
            auto monster = std::dynamic_pointer_cast<Monster>(entity);
            if (monster) {
                addMessage("Você sente a presença de " + monster->name + ".");
            }
        }
    } else {
        addMessage("Caminho bloqueado.");
    }
}

void Game::scanAction() {
    auto entity = map->getEntityAt(player->x, player->y);
    if (entity && entity != player) {
        auto monster = std::dynamic_pointer_cast<Monster>(entity);
        if (monster) {
            addMessage("SCAN: " + monster->getDescription());
            telemetry->sendEvent("SCAN", "", player->x, player->y);
        } else {
            addMessage("SCAN: Nenhuma entidade significativa detectada.");
        }
    } else {
        addMessage("SCAN: Nada de anômalo aqui.");
    }
}

void Game::reportAction() {
    auto entity = map->getEntityAt(player->x, player->y);
    if (entity && entity != player) {
        auto monster = std::dynamic_pointer_cast<Monster>(entity);
        if (monster) {
            std::string monsterTypeStr;
            switch (monster->monsterType) {
                case MonsterType::STONE_WORM: monsterTypeStr = "STONE_WORM"; break;
                case MonsterType::SHADOW_LEAK: monsterTypeStr = "SHADOW_LEAK"; break;
                case MonsterType::DOPPELGANGER: monsterTypeStr = "DOPPELGANGER"; break;
                case MonsterType::VOID_SWARM: monsterTypeStr = "VOID_SWARM"; break;
                default: break;
            }
            bool sent = telemetry->sendEvent("REPORT_MONSTER", monsterTypeStr, player->x, player->y);
            if (sent) {
                addMessage("Relatório enviado. A Muralha aceitou em silêncio (202).");
                map->removeEntity(entity->x, entity->y);
                addMessage(monster->name + " foi removido do Véu.");
            } else {
                addMessage("Falha ao enviar relatório. A Muralha está inalcançável.");
            }
        }
    } else {
        addMessage("Nada para reportar aqui.");
    }
}

void Game::handleInput() {
    int ch = _getch();
    switch (ch) {
        case 'w': case 'W': movePlayer(0, -1); break;
        case 's': case 'S': movePlayer(0, 1); break;
        case 'a': case 'A': movePlayer(-1, 0); break;
        case 'd': case 'D': movePlayer(1, 0); break;
        case 'r': case 'R': reportAction(); break;
        case 'f': case 'F': scanAction(); break;   // 'f' para scan
        case 'q': case 'Q': running = false; break;
        default: addMessage("Comando desconhecido."); break;
    }
}

void Game::run() {
    while (running) {
        render();
        handleInput();
    }
}
