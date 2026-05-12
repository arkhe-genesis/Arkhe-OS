# app/src/main/jni/CMakeLists.txt
cmake_minimum_required(VERSION 3.22.1)
project(arkhe_native)

# Configurações C++
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Flags de compilação para segurança
add_compile_options(
    -Wall -Wextra -Werror
    -fstack-protector-strong
    -D_FORTIFY_SOURCE=2
    -fvisibility=hidden
)

# Linker flags para hardening
add_link_options(
    -Wl,-z,relro,-z,now
    -Wl,--hash-style=both
)

# Incluir headers do ARKHE core
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${ANDROID_NDK}/sources/android/native_app_glue
)

# Biblioteca Falcon-1024 via liboqs (submodule)
if(ENABLE_FALCON)
    add_subdirectory(lib/liboqs)
    include_directories(lib/liboqs/include)
endif()

# Biblioteca BN254 para pairing (submodule)
if(ENABLE_BN254)
    add_subdirectory(lib/bn254)
    include_directories(lib/bn254/include)
endif()

# Biblioteca principal do ARKHE nativo
add_library(arkhe_core SHARED
    arkhe_core.cpp
    crypto_falcon.cpp
    pairing_bn254.cpp
    compression_native.cpp
)

# Linkar bibliotecas
target_link_libraries(arkhe_core
    android
    log
    z  # zlib para compressão

    # Crypto libraries
    ${CMAKE_DL_LIBS}

    # Optional: Falcon-1024
    $<$<BOOL:${ENABLE_FALCON}>:oqs>

    # Optional: BN254 pairing
    $<$<BOOL:${ENABLE_BN254}>:bn254>
)

# Definir símbolos exportados para JNI
target_compile_definitions(arkhe_core PRIVATE
    ARKHE_VERSION="4.3.5"
    ENABLE_TEE=1
)

# Instalar biblioteca no local correto para Android
install(TARGETS arkhe_core
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
cmake_minimum_required(VERSION 3.22.1)
project(arkhe_native)

set(CMAKE_CXX_STANDARD 17)

add_library(arkhe_core SHARED
    arkhe_core.cpp
    crypto_falcon.cpp
)

target_link_libraries(arkhe_core
    log
)
