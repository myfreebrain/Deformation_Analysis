# 依赖项管理文件

# 查找和设置基础依赖项
function(find_basic_dependencies)
    # Boost库
    find_package(Boost REQUIRED COMPONENTS
        algorithm
        filesystem
        program_options
        system
        thread
    )
    
    # Eigen库
    find_package(Eigen3 REQUIRED)
    
    # OpenCV库
    find_package(OpenCV REQUIRED)
    
    # GDAL库
    find_package(GDAL REQUIRED)
    
    # 创建基础依赖的导入目标
    add_library(basic_dependencies INTERFACE)
    target_link_libraries(basic_dependencies INTERFACE
        Boost::boost
        Boost::filesystem
        Boost::program_options
        Boost::system
        Boost::thread
        Eigen3::Eigen
        ${OpenCV_LIBS}
        ${GDAL_LIBRARIES}
    )
    
    target_include_directories(basic_dependencies INTERFACE
        ${Boost_INCLUDE_DIRS}
        ${EIGEN3_INCLUDE_DIR}
        ${OpenCV_INCLUDE_DIRS}
        ${GDAL_INCLUDE_DIRS}
    )
endfunction()

# 查找点云处理相关依赖
function(find_pointcloud_dependencies)
    # PCL库
    find_package(PCL REQUIRED COMPONENTS
        common
        io
        filters
        features
        kdtree
        registration
        segmentation
        surface
    )
    
    # 创建点云处理依赖的导入目标
    add_library(pointcloud_dependencies INTERFACE)
    target_link_libraries(pointcloud_dependencies INTERFACE
        ${PCL_LIBRARIES}
    )
    
    target_include_directories(pointcloud_dependencies INTERFACE
        ${PCL_INCLUDE_DIRS}
    )
    
    target_compile_definitions(pointcloud_dependencies INTERFACE
        ${PCL_DEFINITIONS}
    )
endfunction()

# 查找GUI相关依赖
function(find_gui_dependencies)
    if(BUILD_GUI)
        find_package(Qt5 REQUIRED COMPONENTS
            Core
            Widgets
            Gui
            OpenGL
        )
        
        find_package(OpenGL REQUIRED)
        find_package(GLEW REQUIRED)
        
        # 创建GUI依赖的导入目标
        add_library(gui_dependencies INTERFACE)
        target_link_libraries(gui_dependencies INTERFACE
            Qt5::Core
            Qt5::Widgets
            Qt5::Gui
            Qt5::OpenGL
            ${OPENGL_LIBRARIES}
            ${GLEW_LIBRARIES}
        )
        
        target_include_directories(gui_dependencies INTERFACE
            ${Qt5Core_INCLUDE_DIRS}
            ${Qt5Widgets_INCLUDE_DIRS}
            ${Qt5Gui_INCLUDE_DIRS}
            ${Qt5OpenGL_INCLUDE_DIRS}
            ${OPENGL_INCLUDE_DIR}
            ${GLEW_INCLUDE_DIRS}
        )
    endif()
endfunction()

# 查找科学计算相关依赖
function(find_scientific_dependencies)
    find_package(GSL REQUIRED)
    find_package(HDF5 REQUIRED)
    find_package(LAPACK REQUIRED)
    
    # 创建科学计算依赖的导入目标
    add_library(scientific_dependencies INTERFACE)
    target_link_libraries(scientific_dependencies INTERFACE
        ${GSL_LIBRARIES}
        ${HDF5_LIBRARIES}
        ${LAPACK_LIBRARIES}
    )
    
    target_include_directories(scientific_dependencies INTERFACE
        ${GSL_INCLUDE_DIRS}
        ${HDF5_INCLUDE_DIRS}
    )
endfunction()

# 执行所有依赖项查找
find_basic_dependencies()
find_pointcloud_dependencies()
find_gui_dependencies()
find_scientific_dependencies()

# 创建一个总依赖目标
add_library(all_dependencies INTERFACE)
target_link_libraries(all_dependencies INTERFACE
    basic_dependencies
    pointcloud_dependencies
)

if(BUILD_GUI)
    target_link_libraries(all_dependencies INTERFACE
        gui_dependencies
    )
endif()

target_link_libraries(all_dependencies INTERFACE
    scientific_dependencies
) 