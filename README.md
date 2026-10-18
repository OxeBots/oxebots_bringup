# Oxebots Bringup (`oxebots_bringup`)

Pacote central de inicialização (*launch*) e configuração global de parâmetros da equipe **OxeBots SSL**.
Ele é responsável por orquestrar toda a pilha de software (pontes de rede da SSL-Vision e Game Controller, observador de jogo, filtro de Kalman, visualização RViz, atribuição de papéis, árvores de comportamento, planejamento D* Lite e drivers de comunicação com simuladores ou robôs reais).

---

## 1. Estrutura do Pacote

```text
oxebots_bringup/
├── CMakeLists.txt
├── package.xml
├── README.md
├── config/
│   ├── match_config.yaml         # Configuração padrão (usada quando nenhum time/arquivo é forçado)
│   ├── match_config_blue.yaml    # Configuração dedicada ao Time Azul (is_yellow_team: false)
│   ├── match_config_yellow.yaml  # Configuração dedicada ao Time Amarelo (is_yellow_team: true)
│   └── rviz2_config.rviz         # Layout padrão do RViz2 (campo, robôs, bola, rotas D* e marcadores)
└── launch/
    └── ssl-new.launch.py         # Launch unificado (grSim, ER-Force/Ra, Jogo Real via Rádio e Partida Azul x Amarelo)
```

---

## 2. Arquivos de Configuração (`config/`)

Os arquivos `.yaml` em `config/` centralizam os parâmetros ROS 2 compartilhados por todos os nós da arquitetura.

### 2.1. Parâmetros Globais (`/**:`)
Aplicados a todos os nós que declaram essas chaves (`strategy_node`, `d_star_planner_node`, `role_assigner_node`, `game_observer_node`, `grSim_controller_node`, `ra_controller_node`):

| Parâmetro | Tipo | Valor Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `is_yellow_team` | `bool` | `true` / `false` | Define a cor do time (`false` = Azul, `true` = Amarelo). Ajusta portas do simulador e lado defensivo padrão. |
| `team_size` | `int` | `3` | Quantidade de robôs da equipe. |
| `bt_xml_path` | `string` | `"master_strategy_carry.xml"` | Arquivo XML principal da Behavior Tree executado pelo `strategy_node`. |
| `execution_rate` | `double` | `60.0` | Frequência (Hz) do loop de ticks da Behavior Tree. |

### 2.2. Controle de Simulador (`grSim_controller_node`)
| Parâmetro | Tipo | Valor Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `simulator_ip` | `string` | `"127.0.0.1"` | Endereço IP da máquina rodando o simulador. |
| `simulator_port` | `int` | `10301` | Porta UDP de controle no grSim (`10301` para Azul, ajustada automaticamente para `10302` se `is_yellow_team: true`). |
| `interface_ip` | `string` | `""` | Interface de saída UDP (vazio usa a rota padrão do sistema). |
| `command_topic` | `string` | `"robot_commands"` | Tópico ROS 2 assinado para receber velocidades e comandos de chute. |

### 2.3. Pontes SSL-Vision e Game Controller (`ssl_vision_bridge` / `gc_multicast_bridge`)
| Nó | Parâmetro | Valor Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `ssl_vision_bridge` | `ssl_vision_ip` | `"224.5.23.2"` | Grupo multicast oficial do SSL-Vision / simuladores. |
| `ssl_vision_bridge` | `ssl_vision_port` | `10020` | Porta UDP do SSL-Vision(mudar para 10006 para o jogo real). |
| `ssl_vision_bridge` | `net_interface_address` | `""` | IP da placa de rede local para join multicast (vazio tenta todas as interfaces). |
| `gc_multicast_bridge` | `multicast.address` | `"224.5.23.1"` | Grupo multicast oficial do SSL Game Controller. |
| `gc_multicast_bridge` | `multicast.port` | `10003` | Porta UDP do SSL Game Controller. |

### 2.4. Observador de Jogo (`game_observer_node`)
| Parâmetro | Tipo | Valor Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `robot_amount` | `int` | `3` | Número esperado de robôs aliados. |
| `map_resolution` | `double` | `0.05` | Resolução (em metros/célula, `0.05` = 5 cm) da grade de ocupação `/map` gerada para o D* Lite. |
| `robot_inflation_radius` | `double` | `150.0` | Raio de inflação dos obstáculos (robôs) no mapa estático em milímetros. |
| `vision_topic` | `string` | `"/ssl_vision_bridge/vision_messages"` | Tópico de entrada vindo da ponte de visão. |
| `publisher_topic` | `string` | `"game_data"` | Tópico consolidado publicado com estado de robôs e bola. |
| `referee_topic` | `string` | `"/gc_multicast_bridge/referee_messages"` | Tópico de entrada com comandos do juiz. |

### 2.5. Rádio NRF24 para Robôs Reais (`nrf24_hardware_bridge`)
| Parâmetro | Tipo | Valor Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `radio_rx_address` | `string` | `"ADMIN"` | Endereço RX da estação base (exatamente 5 caracteres). |
| `radio_tx_address` | `string` | `"ESP32"` | Endereço TX dos robôs (exatamente 5 caracteres). |
| `radio_frequency` | `double` | `2.476` | Frequência do canal de rádio em GHz. |
| `radio_rate` | `int` | `3` | Taxa de transmissão configurada via comandos AT no módulo serial USB. |

---

## 3. Launch Unificado (`launch/ssl-new.launch.py`)

O arquivo `ssl-new.launch.py` substitui os antigos launches separados e permite iniciar todo o sistema para **grSim**, **ER-Force (Ra)**, **Jogo Real (Rádio NRF24)** ou **Partida Completa (Azul vs Amarelo)** apenas combinando flags de linha de comando.

### 3.1. Nós Inicializados pelo Launch
1. **`ssl_vision_bridge`** (`ssl_ros_bridge`): Recebe pacotes protobuf UDP do SSL-Vision e publica no ROS 2.
2. **`gc_multicast_bridge`** (`ssl_ros_bridge`): Recebe pacotes protobuf UDP do Game Controller.
3. **`game_observer_node`** (`oxebots_observers`): Processa visão/juiz, publica `/game_data`, `/field_geometry` (QoS `transient_local`) e a grade `/map`.
4. **`field_visualizer_node`** (`oxebots_observers`): Desenha as linhas e dimensões reais do campo no RViz a partir de `/field_geometry`.
5. **Driver de Comunicação (`oxebots_comms`) — selecionado via flag `mode`:**
   * `mode:=grsim` $\rightarrow$ Sobe `grSim_controller_node` (envia velocidades globais para o grSim).
   * `mode:=ra` $\rightarrow$ Sobe `ra_controller_node` (converte velocidades globais para referenciais locais para o simulador ER-Force/Ra).
   * `mode:=game` $\rightarrow$ Sobe `nrf24_bridge_node` (envio via rádio USB NRF24 para os robôs reais) + `ra_controller_node`.
6. **`kalman_filter_node`** (`oxebots_prediction`): Filtragem e predição de posição/velocidade da bola e dos robôs.
7. **`strategy.launch.py`** (`oxebots_strategy`): Sobe, para cada robô (`0, 1, 2`), o trio:
   * `d_star_planner_node_<id>` (Planejamento de trajetória D* Lite / Straight Line)
   * `path_follower_node_<id>` (`movement_calculation_node` — controle linear/angular, chute e proteção dinâmica de área)
   * `strategy_node_<id>` (Execução da Behavior Tree e Blackboard)
8. **`role_assigner_node`** (`oxebots_strategy`): Atribuição dinâmica de papéis com histerese (`/role_assignment`).
9. **`rviz2`** (Opcional): Interface gráfica pré-configurada com `rviz2_config.rviz`.

---

### 3.2. Tabela de Flags (Argumentos de Launch)

| Flag | Valores Aceitos | Padrão | Comportamento |
| :--- | :--- | :--- | :--- |
| `mode` | `grsim`, `ra`, `game` | `grsim` | Escolhe o backend de comunicação: **grSim** (`grsim`), **ER-Force/Ra** (`ra`) ou **Jogo Real c/ Rádio NRF24** (`game`). |
| `invert_sides` | `True`, `False`, `""` | Auto (`False` no `grsim` e `game`, `True` no `ra`) | Inverte as coordenadas do campo (`x = -x`, `y = -y`, `θ += π`) e o lado dos gols. Se omitido, ativa automaticamente apenas no `ra` e fica desativado (`False`) no `grsim` e `game`. Pode ser forçado manualmente em qualquer modo. |
| `config_file` | Caminho para `.yaml` | `match_config.yaml` | Permite passar um arquivo YAML específico. Se vazio, usa `match_config.yaml` (ou o YAML correspondente a `team_color`). |
| `team_color` | `blue`, `yellow`, `""` | `""` (usa o `match_config.yaml`) | Atalho opcional para carregar diretamente `match_config_blue.yaml` ou `match_config_yellow.yaml`. |
| `bt_xml` | Nome do arquivo `.xml` | Valor do YAML (`master_strategy_carry.xml`) | Sobrescreve a árvore de comportamento em tempo de execução sem precisar editar o `.yaml`. |
| `use_rviz` | `True`, `False` | `True` | Abre ou oculta a janela do RViz2 (no modo de time único). |
| `match` | `True`, `False` | `False` | Quando `True`, sobe **os dois times simultaneamente** na mesma máquina isolados por `ROS_DOMAIN_ID` (`0` = Azul, `1` = Amarelo). |
| `rviz_team` | `none`, `blue`, `yellow`, `both` | `none` | Usado quando `match:=True` para escolher qual time abrirá janela do RViz2. |
| `enable_blue` | `True`, `False` | `True` | Usado quando `match:=True` para habilitar/desabilitar a stack do Time Azul. |
| `enable_yellow` | `True`, `False` | `True` | Usado quando `match:=True` para habilitar/desabilitar a stack do Time Amarelo. |

---

## 4. Guia Rápido de Comandos (Exemplos de Uso)

### Cenário 1: Simulação no grSim (Padrão)
Usa as configurações de `config/match_config.yaml`, `grSim_controller_node` e `invert_sides:=False`:
```bash
ros2 launch oxebots_bringup ssl-new.launch.py
```
Para escolher explicitamente o YAML do time azul ou amarelo:
```bash
ros2 launch oxebots_bringup ssl-new.launch.py team_color:=blue
ros2 launch oxebots_bringup ssl-new.launch.py team_color:=yellow
```

### Cenário 2: Simulação no ER-Force / Ra
Troca automaticamente para o `ra_controller_node` e já define `invert_sides:=True` por padrão:
```bash
ros2 launch oxebots_bringup ssl-new.launch.py mode:=ra
```
Se quiser rodar no Ra sem inverter os lados:
```bash
ros2 launch oxebots_bringup ssl-new.launch.py mode:=ra invert_sides:=False
```

### Cenário 3: Jogo Real / Bancada com Rádio NRF24 (`mode:=game`)
Sobe o `nrf24_bridge_node` (porta serial USB) junto com o `ra_controller_node` e mantém `invert_sides:=False` por padrão:
```bash
ros2 launch oxebots_bringup ssl-new.launch.py mode:=game
```
Se na partida real o time trocar de lado na quadra e precisar inverter:
```bash
ros2 launch oxebots_bringup ssl-new.launch.py mode:=game invert_sides:=True
```

### Cenário 4: Testar outra Behavior Tree ou Rodar sem RViz
```bash
ros2 launch oxebots_bringup ssl-new.launch.py bt_xml:=simple_attack.xml use_rviz:=False
```

### Cenário 5: Partida Completa Simulada (Time Azul vs Time Amarelo)
Você pode usar o script `./run_match.sh` na raiz do workspace (que redireciona automaticamente para o DevContainer e aciona `ssl-new.launch.py match:=True`):
```bash
# Sobe Azul (ROS_DOMAIN_ID=0) e Amarelo (ROS_DOMAIN_ID=1) sem RViz
./run_match.sh

# Sobe a partida abrindo o RViz para o time azul
./run_match.sh rviz_team:=blue

# Sobe a partida no simulador ER-Force / Ra
./run_match.sh mode:=ra
```
Ou diretamente via `ros2 launch`:
```bash
ros2 launch oxebots_bringup ssl-new.launch.py match:=True rviz_team:=blue
```
