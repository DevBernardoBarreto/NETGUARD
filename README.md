🛡️ NETGUARD

Monitor de segurança de rede local para pequenos negócios. Descobre os dispositivos conectados, compara com uma lista de autorizados e gera alertas quando aparece um desconhecido.

⚠️ Projeto defensivo (Blue Team). Use apenas em redes que você tem autorização para monitorar. O NETGUARD só observa: não ataca, não explora falhas e não bloqueia dispositivos.

Funcionalidades
Varredura manual e monitoramento automático com intervalo configurável
Cadastro de dispositivos autorizados por MAC Address
Alertas de dispositivos desconhecidos, sem repetição a cada varredura
Histórico de varreduras e alertas em SQLite
Dashboard escuro com cards e tabelas
Tecnologias

!É obrigatório a instalação do nmap para a varredura da rede, é possivel fazer a instalação por meio do site https://nmap.org/

Python · Nmap (python-nmap) · SQLite · Tkinter

Instalação

Requisitos: Python 3.10+ e Nmap (com Npcap).

powershell
git clone https://github.com/SEU-USUARIO/NETGUARD.git
cd NETGUARD
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py

Execute o terminal como Administrador para o Nmap conseguir ler os MACs.

Como usar
Clique em Iniciar varredura.
Autorize seus aparelhos na aba Dispositivos na rede.
Confira os desconhecidos na aba Alertas.
Ative o Monitoramento automático se quiser vigilância contínua.
Estrutura
NETGUARD/
├── main.py          # Ponto de entrada
├── config.py        # Configurações
├── scanner.py       # Varredura com Nmap
├── banco.py         # SQLite
├── dispositivos.py  # Dispositivos autorizados
├── alertas.py       # Detecção e registro de alertas
├── interface.py     # Dashboard Tkinter
└── test_netguard.py # Testes (python -m unittest -v)
Limitações
Assume rede /24.
Celulares com endereço MAC privado/aleatório aparecem como novos dispositivos.
Licença

Projeto acadêmico e de portfólio. Defina a licença de sua preferência (ex.: MIT).
