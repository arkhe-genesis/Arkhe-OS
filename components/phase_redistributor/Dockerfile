FROM debian:bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libyaml-cpp-dev \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install LibTorch
WORKDIR /opt
RUN wget https://download.pytorch.org/libtorch/cpu/libtorch-cxx11-abi-shared-with-deps-2.2.0%2Bcpu.zip -O libtorch.zip && \
    unzip libtorch.zip && \
    rm libtorch.zip

ENV LIBTORCH_PATH=/opt/libtorch
ENV CMAKE_PREFIX_PATH=/opt/libtorch

# Build application
WORKDIR /app
COPY . .

RUN mkdir build && cd build && \
    cmake .. -DCMAKE_PREFIX_PATH=/opt/libtorch -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc)

CMD ["./build/tzinor_gateway"]
