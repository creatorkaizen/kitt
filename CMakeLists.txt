# Kitt — top-level CMake orchestration layer.
#
# This is an optional orchestration layer (KITT_ARCHITECTURE.md
# section 4): the real build target lives in src/windows. Root
# CMakeLists.txt exists so the project can be configured/built from
# the repository root with a single `cmake` invocation, and so
# future non-Windows-native pieces (docs generation hooks, packaging
# glue, etc.) have one place to attach to without touching the
# native subproject.
#
# Kitt v1 targets Windows x64 only (KITT_ARCHITECTURE.md section 23).

cmake_minimum_required(VERSION 3.20)

project(Kitt
    VERSION 0.1.0
    DESCRIPTION "Kitt — Ukrainian mnemonic keyboard layout for Windows"
    LANGUAGES C
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

if(NOT WIN32)
    message(FATAL_ERROR "Kitt's native layer targets Windows only.")
endif()

add_subdirectory(src/windows)
