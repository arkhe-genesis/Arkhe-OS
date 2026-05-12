#pragma once

#include <string>
#include <unistd.h>
#include <sys/wait.h>
#include "fd.hpp"

#define ARK_COMMAND_CAPTURE(cmd) \
    [](const std::string& command) -> ark::Result<std::string> { \
        int pipefd[2]; if (pipe(pipefd)) return ark::Result<std::string>{"", "pipe failed"}; \
        pid_t pid = fork(); \
        if (pid == 0) { \
            ::close(pipefd[0]); dup2(pipefd[1], STDOUT_FILENO); ::close(pipefd[1]); \
            execl("/bin/sh", "sh", "-c", command.c_str(), nullptr); _exit(127); \
        } \
        ::close(pipefd[1]); \
        std::string out; char buf[4096]; \
        while (ssize_t n = ::read(pipefd[0], buf, sizeof(buf))) out.append(buf, n); \
        ::close(pipefd[0]); \
        int status; waitpid(pid, &status, 0); \
        if (WIFEXITED(status) && WEXITSTATUS(status) != 0) return ark::Result<std::string>{"", "cmd failed"}; \
        return ark::Result<std::string>{out, ""}; \
    }(cmd)
