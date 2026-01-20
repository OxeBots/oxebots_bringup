import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    declare_is_yellow_arg = DeclareLaunchArgument(
        "is_yellow",
        default_value="false",
        description="Whether the team is yellow (true) or blue (false)",
    )
    is_yellow = LaunchConfiguration("is_yellow")

    bringup_pkg_share = get_package_share_directory("oxebots_bringup")
    strategy_pkg_share = get_package_share_directory("oxebots_strategy")
    bringup_config_file = os.path.join(
        bringup_pkg_share, "config", "ssl_config.yaml"
    )
    rviz_config_file = os.path.join(
        bringup_pkg_share, "config", "rviz2_config.rviz"
    )

    # Communication and Observation Nodes
    grSim_controller_node = Node(
        package="oxebots_comms",
        executable="grSim_controller_node",
        name="grSim_controller_node",
        parameters=[bringup_config_file],
    )

    game_receiver_node = Node(
        package="oxebots_comms",
        executable="game_receiver_node",
        name="game_receiver_node",
        parameters=[bringup_config_file],
    )

    game_observer_node = Node(
        package="oxebots_observers",
        executable="game_observer_node",
        name="game_observer_node",
        parameters=[bringup_config_file],
    )

    gc_receiver_node = Node(
        package="oxebots_comms",
        executable="gc_receiver_node",
        name="gc_receiver_node",
        parameters=[bringup_config_file],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config_file],
        output="screen",
    )

    # Include Strategy Launch File
    strategy_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(strategy_pkg_share, "launch", "strategy.launch.py")
        ),
        launch_arguments={"is_yellow": is_yellow}.items(),
    )

    ld.add_action(declare_is_yellow_arg)
    ld.add_action(game_receiver_node)
    ld.add_action(grSim_controller_node)
    ld.add_action(game_observer_node)
    ld.add_action(strategy_launch)
    ld.add_action(gc_receiver_node)
    ld.add_action(rviz_node)

    return ld
