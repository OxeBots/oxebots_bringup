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

"""Unified launch file for the oxebots_bringup package."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def create_team_stack(
    config_file,
    strategy_pkg_share,
    rviz_config_file,
    mode,
    invert_sides,
    bt_xml,
    use_rviz,
    command_mode='velocity',
):
    """Create the list of nodes and launch actions for a single team stack."""
    vision_bridge = Node(
        package='ssl_ros_bridge',
        executable='vision_bridge_node',
        name='ssl_vision_bridge',
        parameters=[config_file],
        output='screen',
    )

    gc_bridge = Node(
        package='ssl_ros_bridge',
        executable='gc_multicast_bridge_node',
        name='gc_multicast_bridge',
        parameters=[config_file],
        output='screen',
    )

    game_observer = Node(
        package='oxebots_observers',
        executable='game_observer_node',
        name='game_observer_node',
        parameters=[config_file, {'invert_sides': invert_sides}],
    )

    field_visualizer = Node(
        package='oxebots_observers',
        executable='field_visualizer_node',
        name='field_visualizer_node',
    )

    # Select communication backend according to mode ('grsim', 'ra', or 'game')
    comm_nodes = []
    if mode == 'ra':
        ra_controller = Node(
            package='oxebots_comms',
            executable='ra_controller_node',
            name='ra_controller_node',
            parameters=[config_file],
        )
        comm_nodes.append(ra_controller)
    elif mode == 'game':
        nrf24_bridge = Node(
            package='oxebots_comms',
            executable='nrf24_bridge_node',
            name='nrf24_hardware_bridge',
            parameters=[config_file, {'command_mode': command_mode}],
            output='screen',
        )
        ra_controller = Node(
            package='oxebots_comms',
            executable='ra_controller_node',
            name='ra_controller_node',
            parameters=[config_file],
        )
        comm_nodes.extend([nrf24_bridge, ra_controller])
    else:
        grsim_controller = Node(
            package='oxebots_comms',
            executable='grSim_controller_node',
            name='grSim_controller_node',
            parameters=[config_file],
        )
        comm_nodes.append(grsim_controller)

    kalman_filter = Node(
        package='oxebots_prediction',
        executable='kalman_filter_node',
        name='kalman_filter_node',
        parameters=[config_file],
    )

    strategy_args = {
        'config_file': config_file,
        'invert_sides': 'True' if invert_sides else 'False',
    }
    if bt_xml:
        strategy_args['bt_xml'] = bt_xml

    strategy_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(strategy_pkg_share, 'launch', 'strategy.launch.py')
        ),
        launch_arguments=strategy_args.items(),
    )

    role_assigner = Node(
        package='oxebots_strategy',
        executable='role_assigner_node',
        name='role_assigner_node',
        parameters=[config_file],
        output='screen',
    )

    nodes = [
        vision_bridge,
        gc_bridge,
        *comm_nodes,
        game_observer,
        field_visualizer,
        kalman_filter,
        strategy_launch,
        role_assigner,
    ]

    if use_rviz:
        rviz = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen',
        )
        nodes.append(rviz)

    return nodes


def launch_setup(context, *args, **kwargs):
    """Resolve launch arguments at runtime and return the launch actions."""
    bringup_pkg_share = get_package_share_directory('oxebots_bringup')
    strategy_pkg_share = get_package_share_directory('oxebots_strategy')

    rviz_config_file = os.path.join(bringup_pkg_share, 'config', 'rviz2_config.rviz')

    config_file = LaunchConfiguration('config_file').perform(context).strip()
    team_color = LaunchConfiguration('team_color').perform(context).strip().lower()
    bt_xml = LaunchConfiguration('bt_xml').perform(context).strip()
    use_rviz = (
        LaunchConfiguration('use_rviz').perform(context).strip().lower()
        in ['true', '1', 'yes']
    )
    mode = LaunchConfiguration('mode').perform(context).strip().lower()
    command_mode = (
        LaunchConfiguration('command_mode').perform(context).strip().lower()
    )
    invert_sides_raw = (
        LaunchConfiguration('invert_sides').perform(context).strip().lower()
    )
    is_match = (
        LaunchConfiguration('match').perform(context).strip().lower()
        in ['true', '1', 'yes']
    )

    # Default invert_sides to True only for 'ra', and False for 'grsim' and 'game'
    if invert_sides_raw in ['true', '1', 'yes']:
        invert_sides = True
    elif invert_sides_raw in ['false', '0', 'no']:
        invert_sides = False
    else:
        invert_sides = mode == 'ra'

    # Full match mode: launch Blue and Yellow stacks in separate ROS_DOMAIN_IDs
    if is_match:
        rviz_team = LaunchConfiguration('rviz_team').perform(context).strip().lower()
        enable_blue = (
            LaunchConfiguration('enable_blue').perform(context).strip().lower()
            in ['true', '1', 'yes']
        )
        enable_yellow = (
            LaunchConfiguration('enable_yellow').perform(context).strip().lower()
            in ['true', '1', 'yes']
        )

        actions = []
        if enable_blue:
            blue_config = os.path.join(
                bringup_pkg_share, 'config', 'match_config_blue.yaml'
            )
            blue_rviz = rviz_team in ['blue', 'both']
            blue_nodes = create_team_stack(
                blue_config,
                strategy_pkg_share,
                rviz_config_file,
                mode,
                invert_sides,
                bt_xml,
                blue_rviz,
                command_mode=command_mode,
            )
            actions.append(
                GroupAction([
                    SetEnvironmentVariable('ROS_DOMAIN_ID', '0'),
                    *blue_nodes,
                ])
            )

        if enable_yellow:
            yellow_config = os.path.join(
                bringup_pkg_share, 'config', 'match_config_yellow.yaml'
            )
            yellow_rviz = rviz_team in ['yellow', 'both']
            yellow_nodes = create_team_stack(
                yellow_config,
                strategy_pkg_share,
                rviz_config_file,
                mode,
                invert_sides,
                bt_xml,
                yellow_rviz,
                command_mode=command_mode,
            )
            actions.append(
                GroupAction([
                    SetEnvironmentVariable('ROS_DOMAIN_ID', '1'),
                    *yellow_nodes,
                ])
            )

        return actions

    # Single-team mode
    if not config_file:
        if team_color == 'yellow':
            config_file = os.path.join(
                bringup_pkg_share, 'config', 'match_config_yellow.yaml'
            )
        elif team_color == 'blue':
            config_file = os.path.join(
                bringup_pkg_share, 'config', 'match_config_blue.yaml'
            )
        else:
            config_file = os.path.join(
                bringup_pkg_share, 'config', 'match_config.yaml'
            )

    return create_team_stack(
        config_file,
        strategy_pkg_share,
        rviz_config_file,
        mode,
        invert_sides,
        bt_xml,
        use_rviz,
        command_mode=command_mode,
    )


def generate_launch_description():
    """Declare launch arguments and initialize the opaque launch setup."""
    declare_mode_arg = DeclareLaunchArgument(
        'mode',
        default_value='grsim',
        description="Communication mode: 'grsim' (default), 'ra', or 'game'",
    )

    declare_command_mode_arg = DeclareLaunchArgument(
        'command_mode',
        default_value='velocity',
        description="Radio command format: 'velocity' (vx/vy/w) or 'point' (trajectory setpoint)",
    )

    declare_invert_sides_arg = DeclareLaunchArgument(
        'invert_sides',
        default_value='',
        description=(
            "Invert field sides ('True' or 'False'). "
            "Defaults to True for 'ra' and False for 'grsim'/'game'"
        ),
    )

    declare_match_arg = DeclareLaunchArgument(
        'match',
        default_value='False',
        description=(
            'If True, launches both Blue (ROS_DOMAIN_ID=0) and '
            'Yellow (ROS_DOMAIN_ID=1) teams'
        ),
    )

    declare_rviz_team_arg = DeclareLaunchArgument(
        'rviz_team',
        default_value='none',
        description=(
            "When match:=True, launch RViz for team: 'none', 'blue', "
            "'yellow', or 'both'"
        ),
    )

    declare_enable_blue_arg = DeclareLaunchArgument(
        'enable_blue',
        default_value='True',
        description='When match:=True, enable Blue team stack',
    )

    declare_enable_yellow_arg = DeclareLaunchArgument(
        'enable_yellow',
        default_value='True',
        description='When match:=True, enable Yellow team stack',
    )

    declare_config_file_arg = DeclareLaunchArgument(
        'config_file',
        default_value='',
        description='Path to YAML configuration file (defaults to match_config.yaml)',
    )

    declare_team_color_arg = DeclareLaunchArgument(
        'team_color',
        default_value='',
        description="Optional team color override: 'blue' or 'yellow'",
    )

    declare_bt_xml_arg = DeclareLaunchArgument(
        'bt_xml',
        default_value='',
        description='Behavior Tree XML file name',
    )

    declare_use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='True',
        description='Whether to start RViz2 (in single-team mode)',
    )

    return LaunchDescription([
        declare_mode_arg,
        declare_command_mode_arg,
        declare_invert_sides_arg,
        declare_match_arg,
        declare_rviz_team_arg,
        declare_enable_blue_arg,
        declare_enable_yellow_arg,
        declare_config_file_arg,
        declare_team_color_arg,
        declare_bt_xml_arg,
        declare_use_rviz_arg,
        OpaqueFunction(function=launch_setup),
    ])
