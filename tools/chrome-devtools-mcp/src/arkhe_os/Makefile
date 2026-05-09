CC=gcc
CFLAGS=-Wall -fPIC -shared -ldl -lm
TARGET=libarkhe_alloc.so
DEMO_TARGET=tailslayer_demo
CXX=g++
CXXFLAGS=-Wall -std=c++20 -pthread -I../../include -I.
CFLAGS=-Wall -fPIC -shared -ldl -lm

all: $(TARGET) $(DEMO_TARGET)

$(TARGET): arkhe_alloc.c
	$(CC) $(CFLAGS) -o $(TARGET) arkhe_alloc.c

$(DEMO_TARGET): tailslayer_arkhe_demo.cpp arkhe_hal.c
	$(CXX) $(CXXFLAGS) -o $(DEMO_TARGET) tailslayer_arkhe_demo.cpp arkhe_hal.c

clean:
	rm -f $(TARGET) $(DEMO_TARGET)

inject: $(TARGET)
	@echo "🜏 Injecting Arkhe Allocator into shell..."
	@echo "Run your commands with: LD_PRELOAD=./$(TARGET) <command>"
