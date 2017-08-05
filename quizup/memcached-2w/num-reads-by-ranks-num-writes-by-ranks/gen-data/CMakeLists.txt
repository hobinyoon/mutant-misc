cmake_minimum_required(VERSION 2.8)
project(obj-pop-rank)

file(GLOB_RECURSE sources src/*.cpp)

add_executable(obj-pop-rank ${sources})

target_compile_options(obj-pop-rank PUBLIC -Wall -Werror -std=gnu++11)

# http://stackoverflow.com/questions/10984442/how-to-detect-c11-support-of-a-compiler-with-cmake/20165220#20165220
set_property(TARGET obj-pop-rank PROPERTY CXX_STANDARD 11)

find_package(Boost COMPONENTS
	date_time
	filesystem
	program_options
	regex
	system
	timer
	REQUIRED)

target_link_libraries(obj-pop-rank PUBLIC
	${Boost_LIBRARIES}
	yaml-cpp
	)
