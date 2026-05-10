cmake_minimum_required(VERSION 3.20)
project(ARKHE_OS VERSION 4.3.8 LANGUAGES C CXX)

# Configurações do projeto
set(CMAKE_C_STANDARD 17)
set(CMAKE_CXX_STANDARD 20)
set(WINDOWS_TARGET_VERSION "10.0.22621.0")

# Encontrar WDK/SDK
find_package(WDK REQUIRED)
find_package(WindowsSDK REQUIRED)

# Opções de build
option(BUILD_DRIVER "Build kernel driver" ON)
option(BUILD_USERSPACE "Build userspace libraries" ON)
option(BUILD_CLI "Build CLI tools" ON)
option(BUILD_SERVICES "Build Windows services" ON)
option(BUILD_TESTS "Build tests" ON)

# =============================================================================
# KERNEL DRIVER
# =============================================================================
if(BUILD_DRIVER)
    message(STATUS "Building ARKHE kernel driver...")

    add_wdk_driver(arkhe_kernel
        kernel/driver/DriverEntry.c
        kernel/driver/DeviceInterface.c
        kernel/driver/IoControl.c
        kernel/modules/temporal/ChainManager.c
        kernel/modules/temporal/MerkleTree.c
        kernel/modules/consensus/ConsensusEngine.c
        kernel/modules/consensus/OracleEvaluator.c
        kernel/modules/routing/DijkstraCore.c
        kernel/crypto/SHA3_256.c
        kernel/crypto/BN128_Field.c
        kernel/crypto/BN128_Pairing.c
        kernel/crypto/FalconVerify.c
    )

    target_include_directories(arkhe_kernel PRIVATE
        ${CMAKE_SOURCE_DIR}/include
        ${WDF_INCLUDE_DIRS}
    )

    target_link_libraries(arkhe_kernel PRIVATE
        ${WDF_LIBRARIES}
        bcrypt.lib
        ntoskrnl.lib
        hal.lib
    )

    set_target_properties(arkhe_kernel PROPERTIES
        INCLUDE_WDM_HEADERS ON
        SDB_APP_COMPAT_SXS_MANIFEST FALSE
    )

    # Gerar .inf para instalação do driver
    wdk_generate_driver_package(arkhe_kernel)
endif()

# =============================================================================
# USERSPACE LIBRARY
# =============================================================================
if(BUILD_USERSPACE)
    message(STATUS "Building libarkhe shared library...")

    add_library(arkhe_shared SHARED
        userspace/libarkhe/src/temporal.c
        userspace/libarkhe/src/consensus.c
        userspace/libarkhe/src/routing.c
        userspace/libarkhe/src/crypto.c
        userspace/libarkhe/src/merkle.c
    )

    target_include_directories(arkhe_shared PUBLIC
        ${CMAKE_SOURCE_DIR}/userspace/libarkhe/include
    )

    target_link_libraries(arkhe_shared PRIVATE
        bcrypt.lib
        advapi32.lib
    )

    # Static library
    add_library(arkhe_static STATIC
        userspace/libarkhe/src/temporal.c
        userspace/libarkle/src/consensus.c
        userspace/libarkle/src/routing.c
    )
endif()

# =============================================================================
# CLI TOOL
# =============================================================================
if(BUILD_CLI)
    message(STATUS "Building arkhe CLI...")

    add_executable(arkhe-cli
        userspace/cli/arkhe-cli/main.cpp
        userspace/cli/arkhe-cli/cmd_route.cpp
        userspace/cli/arkhe-cli/cmd_consensus.cpp
        userspace/cli/arkhe-cli/cmd_ledger.cpp
        userspace/cli/arkhe-cli/cmd_block.cpp
        userspace/cli/arkhe-cli/cmd_status.cpp
    )

    target_link_libraries(arkhe-cli PRIVATE
        arkhe_shared
        bcrypt.lib
    )

    # Console/GUI subsystem
    set_target_properties(arkhe-cli PROPERTIES
        WIN32_EXECUTABLE FALSE  # Console app
    )
endif()

# =============================================================================
# WINDOWS SERVICES
# =============================================================================
if(BUILD_SERVICES)
    message(STATUS "Building ARKHE Windows services...")

    # Oracle Service
    add_executable(arkhe-oracle-svc
        userspace/daemons/arkhe-oracle/oracle.cpp
        userspace/services/windows-service/ServiceManager.cpp
    )
    target_link_libraries(arkhe-oracle-svc PRIVATE
        arkhe_static
        advapi32.lib
    )

    # Router Service
    add_executable(arkhe-router-svc
        userspace/daemons/arkhe-router/router.cpp
        userspace/services/windows-service/ServiceManager.cpp
    )

    # Ledger Service
    add_executable(arkhe-ledger-svc
        userspace/daemons/arkhe-ledger/ledger.cpp
        userspace/services/windows-service/ServiceManager.cpp
    )

    # ZK Prover Service
    add_executable(arkhe-zkprover-svc
        userspace/daemons/arkhe-zkprover/prover.cpp
        userspace/services/windows-service/ServiceManager.cpp
    )

    # Instalar como serviços
    foreach(SVC oracle router ledger zkprover)
        install(TARGETS arkhe-${SVC}-svc
            RUNTIME DESTINATION services)
    endforeach()
endif()

# =============================================================================
# TESTS
# =============================================================================
if(BUILD_TESTS)
    enable_testing()

    # Test driver
    add_executable(test_driver_basic
        tests/basic/driver_test.c
    )
    target_link_libraries(test_driver_basic PRIVATE arkhe_shared)
    add_test(NAME driver_basic COMMAND test_driver_basic)

    # Test consensus
    add_executable(test_consensus
        tests/integration/test_consensus.cpp
    )
    target_link_libraries(test_consensus PRIVATE arkhe_shared)
    add_test(NAME consensus_integration COMMAND test_consensus)

    # Test routing
    add_executable(test_routing
        tests/integration/test_routing.cpp
    )
    target_link_libraries(test_routing PRIVATE arkhe_shared)
    add_test(NAME routing_integration COMMAND test_routing)

    # Test merkle
    add_executable(test_merkle
        tests/integration/test_merkle.cpp
    )
    target_link_libraries(test_merkle PRIVATE arkhe_shared)
    add_test(NAME merkle_integration COMMAND test_merkle)

    # Fuzzing targets
    if(LLVM_INCLUDE_DIRS)
        add_executable(fuzz_temporal_msg
            tests/fuzzing/temporal_msg_fuzzer.cpp
        )
        target_compile_options(fuzz_temporal_msg PRIVATE -fsanitize=fuzzer)
        target_link_options(fuzz_temporal_msg PRIVATE -fsanitize=fuzzer)
    endif()
endif()

# =============================================================================
# INSTALLATION
# =============================================================================
install(TARGETS arkhe-cli RUNTIME DESTINATION bin)
install(TARGETS arkhe_shared RUNTIME DESTINATION lib)
install(DIRECTORY include/ DESTINATION include/arkhe)

# Install PowerShell module
install(FILES scripts/ArkhePS.psm1
    DESTINATION ${CMAKE_INSTALL_PREFIX}/Modules/Arkhe)

# Generate NSIS installer
if(WIN32)
    set(CPACK_GENERATOR "ZIP")
    set(CPACK_PACKAGE_NAME "ARKHE-OS")
    set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
    include(CPack)
endif()
