"""config.py - Configurações gerais do NETGUARD.

Centralizar os valores aqui evita "números mágicos" espalhados pelo código.
"""
from pathlib import Path

PASTA_PROJETO = Path(__file__).resolve().parent
PASTA_BANCO = PASTA_PROJETO / "database"
CAMINHO_BANCO = PASTA_BANCO / "netguard.db"

# Monitoramento periódico (em minutos)
INTERVALO_PADRAO_MIN = 5
INTERVALO_MINIMO_MIN = 1
INTERVALO_MAXIMO_MIN = 1440

# -sn = "ping scan": só descobre quem está ligado, NÃO testa portas.
ARGUMENTOS_NMAP = "-sn"

# Quantos alertas carregar na tela
LIMITE_ALERTAS_TELA = 200
