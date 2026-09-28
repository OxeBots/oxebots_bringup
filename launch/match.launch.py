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


def launch_setup(context, *args, **kwargs):
    bringup_pkg_share = get_package_share_directory("oxebots_bringup")
    ssl_new_launch_path = os.path.join(bringup_pkg_share, "launch", "ssl-new.launch.py")

    bt_xml = LaunchConfiguration("bt_xml").perform(context).strip()
    rviz_team = LaunchConfiguration("rviz_team").perform(context).strip().lower()
    enable_blue = LaunchConfiguration("enable_blue").perform(context).strip().lower() in ["true", "1", "yes"]
    enable_yellow = LaunchConfiguration("enable_yellow").perform(context).strip().lower() in ["true", "1", "yes"]

    actions = []

    # Configuração do Time Azul (ROS_DOMAIN_ID = 0)
    if enable_blue:
        blue_rviz = "True" if rviz_team in ["blue", "both"] else "False"
        blue_args = {
            "team_color": "blue",
            "use_rviz": blue_rviz,
        }
        if bt_xml:
            blue_args["bt_xml"] = bt_xml

        blue_group = GroupAction([
            SetEnvironmentVariable("ROS_DOMAIN_ID", "0"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(ssl_new_launch_path),
                launch_arguments=blue_args.items()
            )
        ])
        actions.append(blue_group)

    # Configuração do Time Amarelo (ROS_DOMAIN_ID = 1)
    if enable_yellow:
        yellow_rviz = "True" if rviz_team in ["yellow", "both"] else "False"
        yellow_args = {
            "team_color": "yellow",
            "use_rviz": yellow_rviz,
        }
        if bt_xml:
            yellow_args["bt_xml"] = bt_xml

        yellow_group = GroupAction([
            SetEnvironmentVariable("ROS_DOMAIN_ID", "1"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(ssl_new_launch_path),
                launch_arguments=yellow_args.items()
            )
        ])
        actions.append(yellow_group)

    return actions


def generate_launch_description():
    declare_bt_xml_arg = DeclareLaunchArgument(
        "bt_xml",
        default_value="",
        description="Behavior Tree XML file name (applies to both teams if specified)",
    )

    declare_rviz_team_arg = DeclareLaunchArgument(
        "rviz_team",
        default_value="none",
        description="Launch RViz for team: 'none', 'blue', 'yellow', or 'both'",
    )

    declare_enable_blue_arg = DeclareLaunchArgument(
        "enable_blue",
        default_value="True",
        description="Enable Blue team stack",
    )

    declare_enable_yellow_arg = DeclareLaunchArgument(
        "enable_yellow",
        default_value="True",
        description="Enable Yellow team stack",
    )

    return LaunchDescription([
        declare_bt_xml_arg,
        declare_rviz_team_arg,
        declare_enable_blue_arg,
        declare_enable_yellow_arg,
        OpaqueFunction(function=launch_setup)
    ])
