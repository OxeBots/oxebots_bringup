import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    # Paths
    bringup_pkg_share = get_package_share_directory("oxebots_bringup")
    strategy_pkg_share = get_package_share_directory("oxebots_strategy")
    config_file = os.path.join(bringup_pkg_share, "config", "ssl_config.yaml")

    # Communication and Observation Nodes
    grSim_controller_node = Node(
        package="oxebots_comms",
        executable="grSim_controller_node",
        name="grSim_controller_node",
        parameters=[config_file],
    )

    game_receiver_node = Node(
        package="oxebots_comms",
        executable="game_receiver_node",
        name="game_receiver_node",
        parameters=[config_file],
    )

    game_observer_node = Node(
        package="oxebots_observers",
        executable="game_observer_node",
        name="game_observer_node",
        parameters=[config_file],
    )

    # Include Strategy Launch File
    strategy_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(strategy_pkg_share, "launch", "strategy.launch.py")
        )
    )

    ld.add_action(game_receiver_node)
    ld.add_action(grSim_controller_node)
    ld.add_action(game_observer_node)
    ld.add_action(strategy_launch)

    return ld
