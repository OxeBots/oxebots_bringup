# Copyright 2024 Oxebots
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()

    sender_node = Node(
        package='oxebots_comms',
        executable='sender_node',
        name='sender_bridge_node',
        parameters=[{'port': 10301}],
    )

    game_receiver_node = Node(
        package='oxebots_comms',
        executable='game_receiver_node',
        name='game_receiver_node',
        parameters=[{'port': 10006}, {'robot_amount': 3}, {'is_yellow_team': True}],
    )

    game_observer_node = Node(
        package='oxebots_observers',
        executable='game_observer_node',
        name='game_observer_node',
        parameters=[{'robot_amount': 3}],
    )

    ld.add_action(game_receiver_node)
    ld.add_action(sender_node)
    ld.add_action(game_observer_node)

    return ld
