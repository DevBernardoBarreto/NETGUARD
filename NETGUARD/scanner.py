"""scanner.py - Descoberta de dispositivos na rede local usando o Nmap.

Este módulo SÓ descobre. Não grava no banco e não decide nada.
Usa apenas "ping scan" (-sn): não testa portas nem explora nada.
"""
import socket
import uuid

import nmap

import config


class ErroScanner(Exception):
    """Erro com mensagem amigável, pronta para mostrar ao usuário."""


def detectar_rede():
    """Descobre o IP deste computador e assume uma rede /24 (ex.: 192.168.0.0/24).

    O 'connect' em UDP não envia nenhum pacote: só pergunta ao sistema qual
    interface seria usada.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        ip_local = sock.getsockname()[0]
    except OSError:
        raise ErroScanner("Não foi possível descobrir sua rede. Verifique se está conectado.")
    finally:
        sock.close()
    rede = ".".join(ip_local.split(".")[:3]) + ".0/24"
    return ip_local, rede


def _meu_mac():
    """MAC deste computador (o Nmap não mostra o MAC da própria máquina).

    Atenção: com várias placas de rede pode ser de outra interface.
    """
    numero = uuid.getnode()
    if (numero >> 40) & 1:  # bit indica que o valor foi inventado pelo Python
        return None
    texto = f"{numero:012X}"
    return ":".join(texto[i:i + 2] for i in range(0, 12, 2))


def _chave_ip(ip):
    return tuple(int(p) for p in ip.split("."))


def interpretar_resultado(nm, ip_local=None):
    """Transforma o resultado bruto do Nmap numa lista simples de dicionários."""
    encontrados = []
    for host in nm.all_hosts():
        info = nm[host]
        if info.state() != "up":
            continue
        enderecos = info.get("addresses", {})
        mac = enderecos.get("mac")
        fabricante = ""
        if mac:
            mac = mac.upper()
            fabricante = info.get("vendor", {}).get(enderecos.get("mac"), "")
        elif host == ip_local:
            mac = _meu_mac()
            fabricante = "(este computador)"
        if not mac:
            # Sem MAC não dá para identificar com segurança; usamos o IP como chave.
            mac = f"SEM-MAC-{host}"
        encontrados.append(
            {"ip": host, "mac": mac, "nome": info.hostname() or "", "fabricante": fabricante}
        )
    encontrados.sort(key=lambda d: _chave_ip(d["ip"]))
    return encontrados


def varrer_rede(rede=None):
    """Faz a varredura. Retorna (rede_usada, lista_de_dispositivos)."""
    ip_local, rede_auto = detectar_rede()
    rede = rede or rede_auto

    try:
        nm = nmap.PortScanner()
    except nmap.PortScannerError:
        raise ErroScanner(
            "Nmap não encontrado. Instale em https://nmap.org/download.html "
            "e reinicie o programa."
        )

    try:
        nm.scan(hosts=rede, arguments=config.ARGUMENTOS_NMAP)
    except nmap.PortScannerError as erro:
        raise ErroScanner(f"O Nmap falhou: {erro}")

    return rede, interpretar_resultado(nm, ip_local)
