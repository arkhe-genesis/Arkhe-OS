#ifndef GAME_HPP
#define GAME_HPP

#include <memory>
#include <vector>
#include <string>
#include "map.hpp"
#include "telemetry.hpp"

class Game {
public:
    Game();
    ~Game();
    void run();

private:
    std::unique_ptr<Map> map;
    std::shared_ptr<Player> player;
    std::unique_ptr<Telemetry> telemetry;
    bool running;
    std::vector<std::string> messageLog;

    void render();
    void handleInput();
    void movePlayer(int dx, int dy);
    void scanAction();
    void reportAction();
    void addMessage(const std::string& msg);
    void clearScreen();
};

#endif
