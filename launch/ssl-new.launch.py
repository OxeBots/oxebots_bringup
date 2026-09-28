import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    bringup_pkg_share = get_package_share_directory("oxebots_bringup")
    strategy_pkg_share = get_package_share_directory("oxebots_strategy")
    
    rviz_config_file = os.path.join(bringup_pkg_share, "config", "rviz2_config.rviz")

    config_file = LaunchConfiguration("config_file").perform(context)
    team_color = LaunchConfiguration("team_color").perform(context).strip().lower()
    bt_xml = LaunchConfiguration("bt_xml").perform(context).strip()
    use_rviz = LaunchConfiguration("use_rviz").perform(context).strip().lower() in ["true", "1", "yes"]

    if not config_file:
        if team_color == "yellow":
            config_file = os.path.join(bringup_pkg_share, "config", "match_config_yellow.yaml")
        elif team_color == "blue":
            config_file = os.path.join(bringup_pkg_share, "config", "match_config_blue.yaml")
        else:
            config_file = os.path.join(bringup_pkg_share, "config", "match_config.yaml")

    # 1. Bridge de Visão (A-TEAM)
    vision_bridge = Node(
        package="ssl_ros_bridge",
        executable="vision_bridge_node",
        name="ssl_vision_bridge",
        parameters=[config_file],
        output="screen"
    )

    # 2. Bridge do Juiz (A-TEAM)
    gc_bridge = Node(
        package="ssl_ros_bridge",
        executable="gc_multicast_bridge_node",
        name="gc_multicast_bridge",
        parameters=[config_file],
        output="screen"
    )

    # 3. Game Observer (OxeBots)
    game_observer = Node(
        package="oxebots_observers",
        executable="game_observer_node",
        name="game_observer_node",
        parameters=[config_file],
    )

    # 4. Field Visualizer (OxeBots)
    field_visualizer = Node(
        package="oxebots_observers",
        executable="field_visualizer_node",
        name="field_visualizer_node",
    )

    # 5. grSim Controller (OxeBots)
    grSim_controller = Node(
        package="oxebots_comms",
        executable="grSim_controller_node",
        name="grSim_controller_node",
        parameters=[config_file],
    )

    # 6. Kalman Filter (OxeBots)
    kalman_filter = Node(
        package="oxebots_prediction",
        executable="kalman_filter_node",
        name="kalman_filter_node",
        parameters=[config_file],
    )

    # 7. Include Strategy (Behavior Trees e Planejamento)
    strategy_args = {"config_file": config_file}
    if bt_xml:
        strategy_args["bt_xml"] = bt_xml

    strategy_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(strategy_pkg_share, "launch", "strategy.launch.py")
        ),
        launch_arguments=strategy_args.items()
    )

    # 8. Role Assigner
    role_assigner = Node(
        package="oxebots_strategy",
        executable="role_assigner_node",
        name="role_assigner_node",
        parameters=[config_file],
        output="screen",
    )

    nodes = [
        vision_bridge,
        gc_bridge,
        grSim_controller,
        game_observer,
        field_visualizer,
        kalman_filter,
        strategy_launch,
        role_assigner,
    ]

    # 9. RViz2 (Opcional)
    if use_rviz:
        rviz = Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["-d", rviz_config_file],
            output="screen",
        )
        nodes.append(rviz)

    return nodes


def generate_launch_description():
    declare_config_file_arg = DeclareLaunchArgument(
        "config_file",
        default_value="",
        description="Path to YAML configuration file (overrides team_color)",
    )

    declare_team_color_arg = DeclareLaunchArgument(
        "team_color",
        default_value="",
        description="Team color: 'blue' or 'yellow' (selects match_config_<color>.yaml)",
    )

    declare_bt_xml_arg = DeclareLaunchArgument(
        "bt_xml",
        default_value="",
        description="Behavior Tree XML file name",
    )

    declare_use_rviz_arg = DeclareLaunchArgument(
        "use_rviz",
        default_value="True",
        description="Whether to start RViz2",
    )

    return LaunchDescription([
        declare_config_file_arg,
        declare_team_color_arg,
        declare_bt_xml_arg,
        declare_use_rviz_arg,
        OpaqueFunction(function=launch_setup)
    ])