import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    pkg_dir = get_package_share_directory("oxebots_bringup")
    config_file = os.path.join(pkg_dir, "config", "ssl_config.yaml")

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

    ld.add_action(game_receiver_node)
    ld.add_action(grSim_controller_node)
    ld.add_action(game_observer_node)

    return ld
