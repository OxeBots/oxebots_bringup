#!/usr/bin/env python3

import argparse
import json
import os
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
import xml.etree.ElementTree as ET

try:
    import yaml
except ImportError:
    print("[ERRO] PyYAML não encontrado. Instale com: pacman -S python-yaml ou apt install python3-yaml")
    sys.exit(1)



class SystemNetworkInspector:


    @staticmethod
    def check_loopback_multicast() -> bool:
        try:
            with open("/sys/class/net/lo/flags", "r") as f:
                flags_hex = int(f.read().strip(), 16)
                # 0x1000 é a constante IFF_MULTICAST no kernel Linux
                return bool(flags_hex & 0x1000)
        except Exception:
            return False

    @staticmethod
    def get_primary_ip(mode: str = "local") -> str:
        if mode == "local":
            return "127.0.0.1"
        try:
            # Abre um socket dummy apenas para consultar a tabela de roteamento do kernel
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    @staticmethod
    def inspect_udp_port(port: int) -> Tuple[bool, str]:
        # Tenta identificar o processo dono cm 'ss -ulnp'
        try:
            res = subprocess.run(
                ["ss", "-ulnp", f"sport = :{port}"],
                capture_output=True, text=True, check=True
            )
            lines = res.stdout.strip().splitlines()
            if len(lines) > 1:
                # pega o nome do processo (ex: users:(("grSim",pid=1234,fd=15)))
                raw_line = lines[1]
                if 'users:(("' in raw_line:
                    proc_name = raw_line.split('users:(("')[1].split('"')[0]
                    return True, f"Em uso por '{proc_name}'"
                return True, "Em uso (outro usuário/container)"
        except Exception:
            pass

        # fallback via /proc/net/udp (não depende de ferramentas externas)
        hex_port = f"{port:04X}"
        try:
            with open("/proc/net/udp", "r") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    local_address = parts[1]
                    local_port_hex = local_address.split(":")[1]
                    if local_port_hex == hex_port:
                        return True, "Porta aberta (/proc/net/udp)"
        except Exception:
            pass

        return False, "Livre (Nenhum processo escutando)"

    @classmethod
    def find_free_udp_port(cls, start_port: int, max_tries: int = 50) -> int:
        for port in range(start_port, start_port + max_tries):
            in_use, _ = cls.inspect_udp_port(port)
            if not in_use:
                return port
        raise RuntimeError(f"Nenhuma porta livre encontrada a partir de {start_port}")

# ferramenta de debug, ainda tá quebrada no arch, não validado no ubuntu

class TrafficDebugger:

    @staticmethod
    def sniff_multicast(mcast_ip: str, port: int, interface_ip: str = "", duration: float = 1.5) -> Tuple[int, float, int]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind(("0.0.0.0", port))

            iface = socket.inet_aton(interface_ip) if interface_ip else struct.pack("!I", socket.INADDR_ANY)
            mreq = struct.pack("4s4s", socket.inet_aton(mcast_ip), iface)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.settimeout(0.2)

            packets = 0
            total_bytes = 0
            start_time = time.monotonic()

            while (time.monotonic() - start_time) < duration:
                try:
                    data, _ = sock.recvfrom(4096)
                    packets += 1
                    total_bytes += len(data)
                except socket.timeout:
                    continue

            elapsed = time.monotonic() - start_time
            hz = packets / elapsed if elapsed > 0 else 0.0
            avg_bytes = (total_bytes // packets) if packets > 0 else 0
            return packets, hz, avg_bytes

        except Exception as e:
            return -1, 0.0, 0
        finally:
            sock.close()

# gerancia a config de rede, ainda não validado

class ConfigManager:

    def __init__(self):
        self.script_path = Path(__file__).resolve()
        self.src_config_path = self.script_path.parent.parent / "config" / "match_config.yaml"
        self.install_config_path = self._find_install_config()

    @staticmethod
    def _find_install_config() -> Optional[Path]:
        try:
            from ament_index_python.packages import get_package_share_directory
            share_dir = Path(get_package_share_directory("oxebots_bringup"))
            cfg = share_dir / "config" / "match_config.yaml"
            return cfg if cfg.exists() else None
        except Exception:
            return None

    def load_ros_config(self) -> dict:
        target = self.src_config_path if self.src_config_path.exists() else self.install_config_path
        if not target or not target.exists():
            raise FileNotFoundError("Não foi possível localizar config/match_config.yaml")
        with open(target, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def save_ros_config(self, data: dict):
        """Salva no diretório src/ e, se não for symlink, atualiza também o install/."""
        if self.src_config_path.exists():
            with open(self.src_config_path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
            print(f"[OK] Atualizado em src: {self.src_config_path}")

        if self.install_config_path and self.install_config_path.exists():
            if not self.install_config_path.is_symlink():
                with open(self.install_config_path, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
                print(f"[OK] Atualizado em install: {self.install_config_path}")

    @staticmethod
    def read_grsim_xml() -> Dict[str, str]:
        """
        (Expansão futura): O grSim salva suas configurações em ~/.grsim.xml.
        o objetivo é mudar lá tbm
        """
        grsim_xml = Path.home() / ".grsim.xml"
        if not grsim_xml.exists():
            return {}
        return {"xml_found": str(grsim_xml)}

# vizu dos testes (montado com ia)
def print_mapping_table(cfg: dict, run_sniffer: bool = False):
    grsim_cfg = cfg.get("grSim_controller_node", {}).get("ros__parameters", {})
    vision_cfg = cfg.get("ssl_vision_bridge", {}).get("ros__parameters", {})
    gc_cfg = cfg.get("gc_multicast_bridge", {}).get("ros__parameters", {})

    sim_ip = grsim_cfg.get("simulator_ip", "127.0.0.1")
    blue_port = int(grsim_cfg.get("simulator_port", 10301))
    yellow_port = blue_port + 1  # Convenção do run_match.sh (10301 Azul / 10302 Amarelo)

    vis_ip = vision_cfg.get("ssl_vision_ip", "224.5.23.2")
    vis_port = int(vision_cfg.get("ssl_vision_port", 10020))
    vis_iface = vision_cfg.get("net_interface_address", "")

    gc_ip = gc_cfg.get("multicast.address", "224.5.23.1")
    gc_port = int(gc_cfg.get("multicast.port", 10003))

    # Diagnóstico das portas
    _, vis_status = SystemNetworkInspector.inspect_udp_port(vis_port)
    _, blue_status = SystemNetworkInspector.inspect_udp_port(blue_port)
    _, yellow_status = SystemNetworkInspector.inspect_udp_port(yellow_port)
    _, sim_ctrl_status = SystemNetworkInspector.inspect_udp_port(10300)
    _, legacy_status = SystemNetworkInspector.inspect_udp_port(20011)

    if run_sniffer:
        print("\n[*] Escutando pacotes Multicast na rede (aguarde ~3s)...")
        v_pkts, v_hz, v_bytes = TrafficDebugger.sniff_multicast(vis_ip, vis_port, vis_iface)
        vis_status = f"Ativo ({v_hz:.1f} Hz | {v_bytes}B)" if v_pkts > 0 else "SEM TRÁFEGO (0 pkt/s)"

        g_pkts, g_hz, _ = TrafficDebugger.sniff_multicast(gc_ip, gc_port, vis_iface)
        gc_status = f"Ativo ({g_hz:.1f} Hz)" if g_pkts > 0 else "Sem tráfego (GC fechado?)"
    else:
        _, gc_status = SystemNetworkInspector.inspect_udp_port(gc_port)

    rows = [
        ("Vision multicast address", "ssl_vision_bridge.ssl_vision_ip", vis_ip, "Multicast Grupo"),
        ("Vision multicast port", "ssl_vision_bridge.ssl_vision_port", str(vis_port), vis_status),
        ("Command listen port", "(Legado grSim — Não usado no SSL Novo)", "20011", legacy_status),
        ("Blue Team status send port", "(Feedback robôs Azuis)", "30011", "Opcional"),
        ("Yellow Team status send port", "(Feedback robôs Amarelos)", "30012", "Opcional"),
        ("Simulation control port", "(Teleport / Controle de Simulação)", "10300", sim_ctrl_status),
        ("Blue team control port", "grSim_controller_node.simulator_port (ID=0)", str(blue_port), blue_status),
        ("Yellow team control port", "grSim_controller_node.simulator_port (ID=1)", str(yellow_port), yellow_status),
        ("--- [Game Controller]", "gc_multicast_bridge.multicast.address:port", f"{gc_ip}:{gc_port}", gc_status),
        ("--- [Host do Simulador]", "grSim_controller_node.simulator_ip", sim_ip, "Unicast Destino"),
    ]

    print("\n" + "=" * 118)
    print(f"{'CAMPO NO GRSIM (GUI -> Communication)':<30} | {'PARÂMETRO ROS 2 (match_config.yaml)':<43} | {'VALOR':<18} | {'DIAGNÓSTICO'}")
    print("-" * 118)
    for grsim_field, ros_param, val, status in rows:
        print(f"{grsim_field:<30} | {ros_param:<43} | {val:<18} | {status}")
    print("=" * 118)

    # Checagem extra da interface de loopback
    if not SystemNetworkInspector.check_loopback_multicast():
        print("\n[!] ALERTA: A interface 'lo' está sem a flag MULTICAST ativa!")
        print("    Rode: sudo ip link set lo multicast on")
    else:
        print("\n[OK] Interface 'lo' com suporte a Multicast ativo.")


# cli para cmd
def main():
    parser = argparse.ArgumentParser(description="OxeBots Network Doctor para grSim e ROS 2")
    parser.add_argument("--mode", choices=["local", "lan"], default="local",
                        help="Define IP 127.0.0.1 (local) ou detecta IP da placa de rede (lan)")
    parser.add_argument("--sniff", action="store_true",
                        help="Escuta os pacotes Multicast em tempo real para validar Visão e Juiz")
    parser.add_argument("--apply", action="store_true",
                        help="Aplica automaticamente o IP detectado no match_config.yaml")
    args = parser.parse_args()

    cfg_manager = ConfigManager()
    config_data = cfg_manager.load_ros_config()

    if args.apply:
        target_ip = SystemNetworkInspector.get_primary_ip(args.mode)
        config_data["grSim_controller_node"]["ros__parameters"]["simulator_ip"] = target_ip
        # Define a interface explicitamente em modo local para evitar conflitos com Docker/VPN
        iface_ip = "127.0.0.1" if args.mode == "local" else target_ip
        config_data["ssl_vision_bridge"]["ros__parameters"]["net_interface_address"] = iface_ip
        config_data["gc_multicast_bridge"]["ros__parameters"]["net_interface_address"] = iface_ip
        cfg_manager.save_ros_config(config_data)

    print_mapping_table(config_data, run_sniffer=args.sniff)


if __name__ == "__main__":
    main()