# NETGUARD — Monitor de Segurança de Rede Local

Ferramenta **defensiva (Blue Team)** para pequenos negócios: descobre os dispositivos conectados à rede, compara com uma lista de dispositivos autorizados e gera alertas quando aparece um desconhecido. A decisão sobre o que fazer fica sempre com o responsável.

> ⚠️ Use **somente em redes que você tem autorização para monitorar**. O NETGUARD faz apenas descoberta (`nmap -sn`): não testa portas, não explora falhas e não bloqueia ninguém.

## Funcionalidades
- Varredura manual e monitoramento automático (intervalo configurável, sem travar a janela)
- Lista de dispositivos autorizados (identificados pelo MAC): adicionar, editar, remover
- Status *autorizado* / *desconhecido* para cada dispositivo
- Alertas com IP, MAC, nome, data/hora, tipo e status, sem repetir o mesmo alerta a cada varredura
- Histórico em SQLite (varreduras, dispositivos, alertas)
- Dashboard em tema escuro (Tkinter)

## Requisitos
- Windows com **Python 3.10+** (marque "Add Python to PATH" ao instalar)
- **Nmap** com Npcap: https://nmap.org/download.html

## Instalação (PowerShell, na pasta do projeto)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Se der erro de scripts desabilitados: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

## Executar
```powershell
python main.py
```
Para o Nmap conseguir ler o **MAC Address** dos dispositivos, rode o terminal/VS Code **como Administrador**. Sem isso, alguns dispositivos aparecem sem MAC e não podem ser autorizados.

## Como usar
1. Clique em **Iniciar varredura**.
2. Na aba **Dispositivos na rede**, selecione os que são seus e clique em **Autorizar selecionado**.
3. Dispositivos desconhecidos geram alertas (aba **Alertas**). Depois de verificar, use **Marcar como revisado**.
4. Marque **Monitoramento automático** e escolha o intervalo em minutos.

## Estrutura
| Arquivo | Função |
|---|---|
| `main.py` | Ponto de entrada |
| `config.py` | Configurações (banco, intervalos) |
| `scanner.py` | Varredura com Nmap (só descobre) |
| `banco.py` | Conexão e tabelas do SQLite |
| `dispositivos.py` | Cadastro de autorizados e consultas |
| `alertas.py` | Detecção de desconhecidos e registro de alertas |
| `interface.py` | Dashboard Tkinter |
| `test_netguard.py` | Testes automáticos da lógica |

## Testes
```powershell
python -m unittest -v
```

## Limitações conhecidas
- Assume rede `/24` (ex.: `192.168.0.0/24`) a partir do IP do computador.
- O Nmap não informa o MAC da própria máquina; usamos o MAC do sistema, que pode ser de outra placa se houver várias.
- Dispositivos que trocam de MAC (ex.: "endereço privado" em celulares) aparecem como novos.
- Alerta ativo não se repete até ser revisado ou o dispositivo ser autorizado.
