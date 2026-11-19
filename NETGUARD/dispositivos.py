"""dispositivos.py - Cadastro de dispositivos autorizados (identificados pelo MAC)."""
import re
from contextlib import closing

import banco


def normalizar_mac(mac):
    """Converte 'aa-bb-cc-dd-ee-ff' ou 'aabb.ccdd.eeff' para 'AA:BB:CC:DD:EE:FF'.

    Levanta ValueError se o MAC for inválido.
    """
    texto = (mac or "").strip()
    if not re.fullmatch(r"[0-9A-Fa-f:\-\.]+", texto):
        raise ValueError("MAC inválido. Exemplo correto: AA:BB:CC:DD:EE:FF")
    limpo = re.sub(r"[:\-\.]", "", texto).upper()
    if len(limpo) != 12:
        raise ValueError("MAC inválido. Ele precisa ter 12 dígitos hexadecimais.")
    return ":".join(limpo[i:i + 2] for i in range(0, 12, 2))


def adicionar_autorizado(mac, nome, descricao=""):
    mac = normalizar_mac(mac)
    nome = (nome or "").strip()
    if not nome:
        raise ValueError("Informe um nome para o dispositivo.")
    with closing(banco.conectar()) as con, con:
        existe = con.execute(
            "SELECT 1 FROM dispositivos_autorizados WHERE mac = ?", (mac,)
        ).fetchone()
        if existe:
            raise ValueError("Esse MAC já está cadastrado.")
        con.execute(
            "INSERT INTO dispositivos_autorizados (mac, nome, descricao, criado_em) "
            "VALUES (?, ?, ?, ?)",
            (mac, nome, (descricao or "").strip(), banco.agora()),
        )
        # Se havia alerta ativo para esse MAC, ele deixa de fazer sentido.
        con.execute(
            "UPDATE alertas SET status = 'resolvido' WHERE mac = ? AND status = 'ativo'",
            (mac,),
        )
    return mac


def editar_autorizado(mac, nome, descricao=""):
    mac = normalizar_mac(mac)
    nome = (nome or "").strip()
    if not nome:
        raise ValueError("Informe um nome para o dispositivo.")
    with closing(banco.conectar()) as con, con:
        cur = con.execute(
            "UPDATE dispositivos_autorizados SET nome = ?, descricao = ? WHERE mac = ?",
            (nome, (descricao or "").strip(), mac),
        )
        if cur.rowcount == 0:
            raise ValueError("Dispositivo não encontrado.")


def remover_autorizado(mac):
    mac = normalizar_mac(mac)
    with closing(banco.conectar()) as con, con:
        con.execute("DELETE FROM dispositivos_autorizados WHERE mac = ?", (mac,))


def listar_autorizados():
    with closing(banco.conectar()) as con:
        linhas = con.execute(
            "SELECT * FROM dispositivos_autorizados ORDER BY nome COLLATE NOCASE"
        ).fetchall()
    return [dict(l) for l in linhas]


def obter_macs_autorizados():
    """Conjunto de MACs autorizados (busca rápida na comparação)."""
    with closing(banco.conectar()) as con:
        linhas = con.execute("SELECT mac FROM dispositivos_autorizados").fetchall()
    return {l["mac"] for l in linhas}


def _chave_ip(ip):
    try:
        return tuple(int(p) for p in ip.split("."))
    except (ValueError, AttributeError):
        return (999, 999, 999, 999)


def listar_encontrados_ultima_varredura():
    """Dispositivos vistos na última varredura, já com status autorizado/desconhecido.

    O status é calculado na hora: se você autorizar um dispositivo depois da
    varredura, ele já aparece como autorizado.
    """
    with closing(banco.conectar()) as con:
        linhas = con.execute(
            """
            SELECT e.mac, e.ip, e.nome_host, e.fabricante, e.ultima_vez,
                   CASE WHEN a.mac IS NULL THEN 'desconhecido' ELSE 'autorizado' END AS status,
                   a.nome AS nome_cadastrado
            FROM dispositivos_encontrados e
            LEFT JOIN dispositivos_autorizados a ON a.mac = e.mac
            WHERE e.ultima_varredura_id = (SELECT MAX(id) FROM varreduras)
            """
        ).fetchall()
    resultado = [dict(l) for l in linhas]
    resultado.sort(key=lambda d: _chave_ip(d["ip"]))
    return resultado
