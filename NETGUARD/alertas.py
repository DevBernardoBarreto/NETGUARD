"""alertas.py - Compara a varredura com a lista de autorizados e registra alertas."""
from contextlib import closing

import banco
import config
import dispositivos

TIPO_DESCONHECIDO = "DISPOSITIVO_DESCONHECIDO"


def processar_varredura(lista_encontrados, rede):
    """Salva a varredura, atualiza os dispositivos vistos e cria alertas.

    Regra anti-duplicação: só cria alerta novo se NÃO existir um alerta 'ativo'
    para aquele MAC. Assim o mesmo intruso não gera um alerta a cada varredura.
    O alerta volta a ser possível depois que ele for revisado/resolvido.

    Retorna um dicionário com o resumo da varredura.
    """
    autorizados = dispositivos.obter_macs_autorizados()
    desconhecidos = [d for d in lista_encontrados if d["mac"] not in autorizados]
    novos_alertas = []
    agora = banco.agora()

    with closing(banco.conectar()) as con, con:
        cur = con.execute(
            "INSERT INTO varreduras (data_hora, rede, total_encontrados, total_desconhecidos) "
            "VALUES (?, ?, ?, ?)",
            (agora, rede, len(lista_encontrados), len(desconhecidos)),
        )
        id_varredura = cur.lastrowid

        for d in lista_encontrados:
            con.execute(
                """
                INSERT INTO dispositivos_encontrados
                    (mac, ip, nome_host, fabricante, primeira_vez, ultima_vez, ultima_varredura_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mac) DO UPDATE SET
                    ip = excluded.ip,
                    nome_host = excluded.nome_host,
                    fabricante = excluded.fabricante,
                    ultima_vez = excluded.ultima_vez,
                    ultima_varredura_id = excluded.ultima_varredura_id
                """,
                (d["mac"], d["ip"], d["nome"], d["fabricante"], agora, agora, id_varredura),
            )

        for d in desconhecidos:
            ja_alertado = con.execute(
                "SELECT 1 FROM alertas WHERE mac = ? AND tipo = ? AND status = 'ativo'",
                (d["mac"], TIPO_DESCONHECIDO),
            ).fetchone()
            if ja_alertado:
                continue
            con.execute(
                "INSERT INTO alertas (data_hora, tipo, mac, ip, nome_host, status) "
                "VALUES (?, ?, ?, ?, ?, 'ativo')",
                (agora, TIPO_DESCONHECIDO, d["mac"], d["ip"], d["nome"]),
            )
            novos_alertas.append(d)

    return {
        "id_varredura": id_varredura,
        "total": len(lista_encontrados),
        "desconhecidos": len(desconhecidos),
        "novos_alertas": novos_alertas,
    }


def listar_alertas(limite=None):
    limite = limite or config.LIMITE_ALERTAS_TELA
    with closing(banco.conectar()) as con:
        linhas = con.execute(
            "SELECT * FROM alertas ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()
    return [dict(l) for l in linhas]


def contar_alertas_ativos():
    with closing(banco.conectar()) as con:
        return con.execute(
            "SELECT COUNT(*) FROM alertas WHERE status = 'ativo'"
        ).fetchone()[0]


def marcar_como_revisado(id_alerta):
    with closing(banco.conectar()) as con, con:
        con.execute(
            "UPDATE alertas SET status = 'revisado' WHERE id = ? AND status = 'ativo'",
            (id_alerta,),
        )
