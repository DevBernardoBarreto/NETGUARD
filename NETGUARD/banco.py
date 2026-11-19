"""banco.py - Conexão com o SQLite e criação das tabelas."""
import sqlite3
from contextlib import closing
from datetime import datetime

import config


def agora():
    """Data/hora atual no formato que guardamos no banco."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def conectar():
    """Abre uma conexão nova. Cada função abre e fecha a sua (seguro com threads)."""
    config.PASTA_BANCO.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(config.CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    return conexao


def criar_tabelas():
    with closing(conectar()) as con, con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS dispositivos_autorizados (
                mac         TEXT PRIMARY KEY,
                nome        TEXT NOT NULL,
                descricao   TEXT DEFAULT '',
                criado_em   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS varreduras (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora            TEXT NOT NULL,
                rede                 TEXT,
                total_encontrados    INTEGER,
                total_desconhecidos  INTEGER
            );

            CREATE TABLE IF NOT EXISTS dispositivos_encontrados (
                mac                  TEXT PRIMARY KEY,
                ip                   TEXT,
                nome_host            TEXT,
                fabricante           TEXT,
                primeira_vez         TEXT,
                ultima_vez           TEXT,
                ultima_varredura_id  INTEGER
            );

            CREATE TABLE IF NOT EXISTS alertas (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora  TEXT NOT NULL,
                tipo       TEXT NOT NULL,
                mac        TEXT,
                ip         TEXT,
                nome_host  TEXT,
                status     TEXT NOT NULL DEFAULT 'ativo'
            );
            """
        )


def obter_ultima_varredura():
    """Retorna a última varredura (dict) ou None se nunca houve."""
    with closing(conectar()) as con:
        linha = con.execute(
            "SELECT * FROM varreduras ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return dict(linha) if linha else None
