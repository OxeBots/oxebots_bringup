import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()
    
    bringup_pkg_share = get_package_share_directory("oxebots_bringup")
    strategy_pkg_share = get_package_share_directory("oxebots_strategy")
    
    bringup_config_file = os.path.join(bringup_pkg_share, "config", "match_config.yaml")
    rviz_config_file = os.path.join(bringup_pkg_share, "config", "rviz2_config.rviz")

    # 1. Bridge de Visão (A-TEAM)
    vision_bridge = Node(
        package="ssl_ros_bridge",
        executable="vision_bridge_node",
        name="ssl_vision_bridge",
        parameters=[bringup_config_file],
        output="screen"
    )

    # 2. Bridge do Juiz (A-TEAM)
    gc_bridge = Node(
        package="ssl_ros_bridge",
        executable="gc_multicast_bridge_node",
        name="gc_multicast_bridge",
        parameters=[bringup_config_file],
        output="screen"
    )

    # 3. Game Observer (OxeBots)
    game_observer = Node(
        package="oxebots_observers",
        executable="game_observer_node",
        name="game_observer_node",
        parameters=[bringup_config_file, {"invert_sides": True}],
    )

    # 4. Field Visualizer (OxeBots)
    field_visualizer = Node(
        package="oxebots_observers",
        executable="field_visualizer_node",
        name="field_visualizer_node",
    )

    # 5. RA Controller (OxeBots) - Traduz Global para Local para o ER-Force
    ra_controller = Node(
        package="oxebots_comms",
        executable="ra_controller_node",
        name="ra_controller_node",
        parameters=[bringup_config_file],
    )

    # 6. RViz2
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config_file],
        output="screen",
    )

    # 7. Include Strategy
    strategy_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(strategy_pkg_share, "launch", "strategy.launch.py")
        ),
        launch_arguments={"invert_sides": "True"}.items()
    )

    # 8. Role Assigner
    role_assigner = Node(
        package="oxebots_strategy",
        executable="role_assigner_node",
        name="role_assigner_node",
        parameters=[bringup_config_file],
        output="screen",
    )

    ld.add_action(vision_bridge)
    ld.add_action(gc_bridge)
    ld.add_action(ra_controller)
    ld.add_action(game_observer)
    ld.add_action(field_visualizer)
    ld.add_action(strategy_launch)
    ld.add_action(role_assigner)
    ld.add_action(rviz)

    return ld
