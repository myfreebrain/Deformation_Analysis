cmake_minimum_required(VERSION 3.16)
project(DeformationAnalysis VERSION 0.1.0 LANGUAGES CXX C)

# 定义C++标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 确保使用vcpkg
if(NOT DEFINED CMAKE_TOOLCHAIN_FILE AND DEFINED ENV{VCPKG_ROOT})
    set(CMAKE_TOOLCHAIN_FILE "$ENV{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake" CACHE STRING "")
    message(STATUS "使用vcpkg工具链: ${CMAKE_TOOLCHAIN_FILE}")
endif()

# 设置输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 设置构建类型
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Build type" FORCE)
endif()

# 添加子模块依赖库
include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/Dependencies.cmake)

# 包含头文件目录
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_BINARY_DIR}/include
)

# 选项配置
option(USE_CUDA "使用CUDA加速" OFF)
option(USE_MPI "使用MPI并行计算" OFF)
option(BUILD_GUI "构建图形界面" ON)

# 根据选项配置依赖
if(USE_CUDA)
    find_package(CUDA REQUIRED)
    add_definitions(-DUSE_CUDA)
endif()

if(USE_MPI)
    find_package(MPI REQUIRED)
    add_definitions(-DUSE_MPI)
endif()

if(BUILD_GUI)
    find_package(Qt5 COMPONENTS Core Widgets Gui OpenGL REQUIRED)
    add_definitions(-DBUILD_GUI)
endif()

# 查找核心依赖库
find_package(Eigen3 REQUIRED)
find_package(PCL REQUIRED)
find_package(OpenCV REQUIRED)
find_package(GDAL REQUIRED)
find_package(GSL REQUIRED)

# 添加自定义组件
add_subdirectory(components)

# 安装规则
install(
    DIRECTORY ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/
    DESTINATION bin
    USE_SOURCE_PERMISSIONS
    FILES_MATCHING PATTERN "*"
)

# 打印配置信息
message(STATUS "项目版本: ${PROJECT_VERSION}")
message(STATUS "构建类型: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++编译器: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "CUDA支持: ${USE_CUDA}")
message(STATUS "MPI支持: ${USE_MPI}")
message(STATUS "GUI支持: ${BUILD_GUI}") 