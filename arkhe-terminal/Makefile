CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2
LDFLAGS = -lcurl

# Para Linux/macOS pode precisar de -lpthread se curl usar
# LDFLAGS += -lpthread

SRCS = main.cpp game.cpp map.cpp entity.cpp telemetry.cpp
OBJS = $(SRCS:.cpp=.o)
TARGET = arkhe-terminal

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run
