"""Testes automáticos da lógica (sem interface e sem rede real).

Execute:  python -m unittest -v
Usam um banco temporário, então NÃO mexem no seu banco de verdade.
"""
import tempfile
import unittest
from pathlib import Path

import alertas
import banco
import config
import dispositivos
import scanner


def disp(ip, mac, nome="", fab=""):
    return {"ip": ip, "mac": mac, "nome": nome, "fabricante": fab}


class BaseComBanco(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        config.PASTA_BANCO = Path(self.pasta.name)
        config.CAMINHO_BANCO = Path(self.pasta.name) / "teste.db"
        banco.criar_tabelas()

    def tearDown(self):
        self.pasta.cleanup()


class TestDispositivos(BaseComBanco):
    def test_normalizar_mac(self):
        self.assertEqual(dispositivos.normalizar_mac("aa-bb-cc-dd-ee-ff"), "AA:BB:CC:DD:EE:FF")
        self.assertEqual(dispositivos.normalizar_mac("aabb.ccdd.eeff"), "AA:BB:CC:DD:EE:FF")

    def test_mac_invalido(self):
        for ruim in ["", "xyz", "AA:BB:CC", "GG:BB:CC:DD:EE:FF"]:
            with self.assertRaises(ValueError):
                dispositivos.normalizar_mac(ruim)

    def test_crud(self):
        dispositivos.adicionar_autorizado("aa:bb:cc:dd:ee:01", "PC Caixa", "Operacional")
        with self.assertRaises(ValueError):
            dispositivos.adicionar_autorizado("AA:BB:CC:DD:EE:01", "Duplicado")
        with self.assertRaises(ValueError):
            dispositivos.adicionar_autorizado("AA:BB:CC:DD:EE:02", "  ")
        dispositivos.editar_autorizado("AA:BB:CC:DD:EE:01", "PC Balcão", "Novo")
        lista = dispositivos.listar_autorizados()
        self.assertEqual(len(lista), 1)
        self.assertEqual(lista[0]["nome"], "PC Balcão")
        dispositivos.remover_autorizado("AA:BB:CC:DD:EE:01")
        self.assertEqual(dispositivos.listar_autorizados(), [])


class TestAlertas(BaseComBanco):
    def test_desconhecido_gera_alerta(self):
        dispositivos.adicionar_autorizado("AA:BB:CC:DD:EE:01", "PC")
        r = alertas.processar_varredura(
            [disp("192.168.0.2", "AA:BB:CC:DD:EE:01"), disp("192.168.0.9", "11:22:33:44:55:66")],
            "192.168.0.0/24")
        self.assertEqual(r["total"], 2)
        self.assertEqual(r["desconhecidos"], 1)
        self.assertEqual(len(r["novos_alertas"]), 1)
        self.assertEqual(alertas.contar_alertas_ativos(), 1)

    def test_sem_duplicar_alerta(self):
        lista = [disp("192.168.0.9", "11:22:33:44:55:66")]
        alertas.processar_varredura(lista, "x")
        r2 = alertas.processar_varredura(lista, "x")
        self.assertEqual(len(r2["novos_alertas"]), 0)
        self.assertEqual(len(alertas.listar_alertas()), 1)

    def test_revisado_permite_novo_alerta(self):
        lista = [disp("192.168.0.9", "11:22:33:44:55:66")]
        alertas.processar_varredura(lista, "x")
        alertas.marcar_como_revisado(alertas.listar_alertas()[0]["id"])
        r = alertas.processar_varredura(lista, "x")
        self.assertEqual(len(r["novos_alertas"]), 1)

    def test_autorizar_resolve_alerta_e_muda_status(self):
        alertas.processar_varredura([disp("192.168.0.9", "11:22:33:44:55:66", "tel")], "x")
        dispositivos.adicionar_autorizado("11:22:33:44:55:66", "Celular")
        self.assertEqual(alertas.contar_alertas_ativos(), 0)
        encontrados = dispositivos.listar_encontrados_ultima_varredura()
        self.assertEqual(encontrados[0]["status"], "autorizado")

    def test_lista_so_ultima_varredura_e_ordem_ip(self):
        alertas.processar_varredura([disp("192.168.0.10", "AA:AA:AA:AA:AA:01"),
                                     disp("192.168.0.2", "AA:AA:AA:AA:AA:02")], "x")
        ips = [d["ip"] for d in dispositivos.listar_encontrados_ultima_varredura()]
        self.assertEqual(ips, ["192.168.0.2", "192.168.0.10"])
        alertas.processar_varredura([disp("192.168.0.2", "AA:AA:AA:AA:AA:02")], "x")
        self.assertEqual(len(dispositivos.listar_encontrados_ultima_varredura()), 1)
        self.assertEqual(banco.obter_ultima_varredura()["total_encontrados"], 1)


class Host(dict):
    """Imita o objeto de host do python-nmap."""
    def __init__(self, estado, nome, **dados):
        super().__init__(dados)
        self._estado, self._nome = estado, nome
    def state(self): return self._estado
    def hostname(self): return self._nome


class FakeNmap:
    def __init__(self, hosts): self.hosts = hosts
    def all_hosts(self): return list(self.hosts)
    def __getitem__(self, ip): return self.hosts[ip]


class TestScannerInterpretacao(unittest.TestCase):
    def test_interpreta_resultado(self):
        nm = FakeNmap({
            "192.168.0.10": Host("up", "impressora", addresses={"ipv4": "192.168.0.10", "mac": "aa:bb:cc:00:00:01"},
                                 vendor={"aa:bb:cc:00:00:01": "HP"}),
            "192.168.0.2": Host("up", "", addresses={"ipv4": "192.168.0.2", "mac": "aa:bb:cc:00:00:02"}, vendor={}),
            "192.168.0.7": Host("up", "", addresses={"ipv4": "192.168.0.7"}),
            "192.168.0.8": Host("down", "", addresses={"ipv4": "192.168.0.8"}),
        })
        r = scanner.interpretar_resultado(nm, ip_local="192.168.0.1")
        self.assertEqual([d["ip"] for d in r], ["192.168.0.2", "192.168.0.7", "192.168.0.10"])
        self.assertEqual(r[2]["mac"], "AA:BB:CC:00:00:01")
        self.assertEqual(r[2]["fabricante"], "HP")
        self.assertEqual(r[1]["mac"], "SEM-MAC-192.168.0.7")


if __name__ == "__main__":
    unittest.main()
