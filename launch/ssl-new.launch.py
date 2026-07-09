import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    ld = LaunchDescription()
    
    bringup_pkg_share = get_package_share_directory("oxebots_bringup")
    strategy_pkg_share = get_package_share_directory("oxebots_strategy")
    
    bringup_config_file = os.path.join(bringup_pkg_share, "config", "match_config.yaml")
    rviz_config_file = os.path.join(bringup_pkg_share, "config", "rviz2_config.rviz")

    # Argumento para escolher a árvore
    declare_bt_xml_arg = DeclareLaunchArgument(
        "bt_xml",
        default_value="",
        description="Behavior Tree XML file name",
    )

    # 1. Bridge de Visão (A-TEAM) - Substitui o game_receiver proprietário
    vision_bridge = Node(
        package="ssl_ros_bridge",
        executable="vision_bridge_node",
        name="ssl_vision_bridge",
        parameters=[bringup_config_file],
        output="screen"
    )

    # 2. Bridge do Juiz (A-TEAM) - Substitui o gc_receiver proprietário
    gc_bridge = Node(
        package="ssl_ros_bridge",
        executable="gc_multicast_bridge_node",
        name="gc_multicast_bridge",
        parameters=[bringup_config_file],
        output="screen"
    )

    # 3. Game Observer (OxeBots) - Atua como tradutor e gera o mapa
    game_observer = Node(
        package="oxebots_observers",
        executable="game_observer_node",
        name="game_observer_node",
        parameters=[bringup_config_file],
    )

    # 4. Field Visualizer (OxeBots) - Mantido igual ao original
    field_visualizer = Node(
        package="oxebots_observers",
        executable="field_visualizer_node",
        name="field_visualizer_node",
    )

    # 5. grSim Controller (OxeBots) - Mantido para atuação proprietária
    grSim_controller = Node(
        package="oxebots_comms",
        executable="grSim_controller_node",
        name="grSim_controller_node",
        parameters=[bringup_config_file],
    )

    # Kalman Filter (OxeBots)
    kalman_filter = Node(
        package="oxebots_prediction",
        executable="kalman_filter_node",
        name="kalman_filter_node",
        parameters=[bringup_config_file],
    )

    # 6. RViz2 - Monitoramento visual
    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config_file],
        output="screen",
    )

    # 7. Include Strategy - Mantém Behavior Trees e Planejamento
    strategy_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(strategy_pkg_share, "launch", "strategy.launch.py")
        ),
        launch_arguments={
            "bt_xml": LaunchConfiguration("bt_xml"),
            "config_file": bringup_config_file
        }.items()
    )

    # 8. Role Assigner
    role_assigner = Node(
        package="oxebots_strategy",
        executable="role_assigner_node",
        name="role_assigner_node",
        parameters=[bringup_config_file],
        output="screen",
    )

    # Adicionando na ordem original de processamento
    ld.add_action(declare_bt_xml_arg)
    ld.add_action(vision_bridge)
    ld.add_action(gc_bridge)
    ld.add_action(grSim_controller)
    ld.add_action(game_observer)
    ld.add_action(field_visualizer)
    ld.add_action(kalman_filter)
    ld.add_action(strategy_launch)
    ld.add_action(role_assigner)
    ld.add_action(rviz)

    return ld