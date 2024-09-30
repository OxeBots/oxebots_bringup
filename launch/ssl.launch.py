from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    sender_node = Node(
        package="oxebots_comms",
        executable="sender_node",
        name="sender_bridge_node",
        parameters=[
            {
                "port": 10301
            }
        ]
    )

    game_receiver_node = Node(
        package="oxebots_comms",
        executable="game_receiver_node",
        name="game_receiver_node",
        parameters=[
            {
                "port": 10020
            },
            {
                "robot_amount": 3
            },
            {
                "is_yellow_team": True
            }
        ]
    )

    game_observer_node = Node(
        package="oxebots_observers",
        executable="game_observer_node",
        name="game_observer_node",
        parameters=[
            {
                "robot_amount": 3
            }
        ]
    )

    ld.add_action(game_receiver_node)
    ld.add_action(sender_node)
    ld.add_action(game_observer_node)

    return ld
