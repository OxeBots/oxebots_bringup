cmake_minimum_required(VERSION 3.8)

# "NONE" tells CMake this project has no C/C++ code to compile
project(oxebots_bringup NONE)

find_package(ament_cmake REQUIRED)

set(CMAKE_EXPORT_COMPILE_COMMANDS ${CMAKE_EXPORT_COMPILE_COMMANDS})

install(DIRECTORY
  launch config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
