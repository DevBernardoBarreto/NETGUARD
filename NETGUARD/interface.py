"""interface.py - Dashboard do NETGUARD (Tkinter).

Este arquivo só MOSTRA informações e recebe cliques. A lógica fica nos outros módulos.
A varredura roda numa thread separada para a janela não travar.
"""
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import alertas
import banco
import config
import dispositivos
import scanner

# Paleta: tema escuro, azul/ciano e laranja/vermelho para alertas
FUNDO = "#0b1220"
CARD = "#111c2e"
BORDA = "#1f3150"
TEXTO = "#e2e8f0"
TEXTO_SUAVE = "#8aa0bf"
CIANO = "#22d3ee"
AZUL = "#2563eb"
AZUL_SEL = "#1e3a5f"
LARANJA = "#fb923c"
VERMELHO = "#ef4444"
VERDE = "#34d399"

FONTE = "Segoe UI"


class DialogoDispositivo(tk.Toplevel):
    """Janelinha para cadastrar/editar um dispositivo autorizado."""

    def __init__(self, pai, titulo, ao_salvar, mac="", nome="", descricao="", mac_editavel=True):
        super().__init__(pai)
        self.ao_salvar = ao_salvar
        self.title(titulo)
        self.configure(bg=FUNDO, padx=20, pady=16)
        self.resizable(False, False)

        self.var_mac = tk.StringVar(value=mac)
        self.var_nome = tk.StringVar(value=nome)
        self.var_desc = tk.StringVar(value=descricao)

        campos = [
            ("MAC Address:", self.var_mac, "normal" if mac_editavel else "readonly"),
            ("Nome:", self.var_nome, "normal"),
            ("Descrição:", self.var_desc, "normal"),
        ]
        for i, (rotulo, var, estado) in enumerate(campos):
            ttk.Label(self, text=rotulo).grid(row=i, column=0, sticky="w", pady=5, padx=(0, 10))
            entrada = ttk.Entry(self, textvariable=var, width=36, state=estado)
            entrada.grid(row=i, column=1, pady=5)
            if i == (1 if not mac_editavel else 0):
                entrada.focus_set()

        botoes = ttk.Frame(self)
        botoes.grid(row=3, column=0, columnspan=2, pady=(14, 0), sticky="e")
        ttk.Button(botoes, text="Cancelar", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(botoes, text="Salvar", style="Acento.TButton", command=self._salvar).pack(side="right")

        self.bind("<Return>", lambda e: self._salvar())
        self.bind("<Escape>", lambda e: self.destroy())
        self.transient(pai)
        self.grab_set()
        pai.wait_window(self)

    def _salvar(self):
        try:
            self.ao_salvar(self.var_mac.get(), self.var_nome.get(), self.var_desc.get())
        except ValueError as erro:
            messagebox.showerror("NETGUARD", str(erro), parent=self)
            return
        self.destroy()


class NetGuardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NETGUARD — Monitor de Segurança de Rede")
        self.geometry("1150x720")
        self.minsize(950, 600)
        self.configure(bg=FUNDO)

        self.fila = queue.Queue()
        self.escaneando = False
        self.id_agendamento = None
        self.var_monitorar = tk.BooleanVar(value=False)
        self.var_intervalo = tk.StringVar(value=str(config.INTERVALO_PADRAO_MIN))
        self.var_status = tk.StringVar(value="Pronto. Clique em “Iniciar varredura”.")

        self._configurar_estilo()
        self._montar_cabecalho()
        self._montar_cards()
        self._montar_abas()
        self._montar_rodape()

        self.atualizar_tudo()
        self.after(200, self._verificar_fila)

    # ------------------------------------------------------------------ estilo
    def _configurar_estilo(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=FUNDO, foreground=TEXTO, font=(FONTE, 10))
        s.configure("TFrame", background=FUNDO)
        s.configure("TLabel", background=FUNDO, foreground=TEXTO)
        s.configure("TButton", background=CARD, foreground=TEXTO, bordercolor=BORDA,
                    padding=(12, 6), focuscolor=CARD)
        s.map("TButton", background=[("active", AZUL_SEL), ("disabled", FUNDO)],
              foreground=[("disabled", TEXTO_SUAVE)])
        s.configure("Acento.TButton", background=AZUL, foreground="white",
                    font=(FONTE, 10, "bold"), bordercolor=AZUL)
        s.map("Acento.TButton", background=[("active", "#3b82f6"), ("disabled", BORDA)])
        s.configure("TCheckbutton", background=FUNDO, foreground=TEXTO)
        s.map("TCheckbutton", background=[("active", FUNDO)])
        s.configure("TEntry", fieldbackground=CARD, foreground=TEXTO, insertcolor=TEXTO,
                    bordercolor=BORDA)
        s.map("TEntry", fieldbackground=[("readonly", BORDA)])
        s.configure("TSpinbox", fieldbackground=CARD, foreground=TEXTO, arrowcolor=CIANO,
                    bordercolor=BORDA, background=CARD)
        s.configure("TNotebook", background=FUNDO, borderwidth=0)
        s.configure("TNotebook.Tab", background=CARD, foreground=TEXTO_SUAVE,
                    padding=(16, 8), font=(FONTE, 10, "bold"))
        s.map("TNotebook.Tab", background=[("selected", AZUL_SEL)],
              foreground=[("selected", CIANO)])
        s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXTO,
                    rowheight=28, borderwidth=0)
        s.configure("Treeview.Heading", background=BORDA, foreground=CIANO,
                    font=(FONTE, 10, "bold"), relief="flat")
        s.map("Treeview", background=[("selected", AZUL_SEL)])
        s.map("Treeview.Heading", background=[("active", BORDA)])
        s.configure("Vertical.TScrollbar", background=BORDA, troughcolor=CARD,
                    arrowcolor=CIANO, bordercolor=CARD)

    # ------------------------------------------------------------- componentes
    def _montar_cabecalho(self):
        topo = ttk.Frame(self, padding=(20, 16, 20, 6))
        topo.pack(fill="x")

        titulos = ttk.Frame(topo)
        titulos.pack(side="left")
        tk.Label(titulos, text="NETGUARD", font=(FONTE, 22, "bold"), fg=CIANO, bg=FUNDO).pack(anchor="w")
        tk.Label(titulos, text="Monitor de segurança da rede local", font=(FONTE, 10),
                 fg=TEXTO_SUAVE, bg=FUNDO).pack(anchor="w")

        controles = ttk.Frame(topo)
        controles.pack(side="right")
        self.botao_varredura = ttk.Button(controles, text="⟳  Iniciar varredura",
                                          style="Acento.TButton", command=self.iniciar_varredura)
        self.botao_varredura.grid(row=0, column=0, padx=(0, 18))
        ttk.Checkbutton(controles, text="Monitoramento automático", variable=self.var_monitorar,
                        command=self._alternar_monitoramento).grid(row=0, column=1, padx=(0, 8))
        ttk.Label(controles, text="a cada").grid(row=0, column=2)
        ttk.Spinbox(controles, from_=config.INTERVALO_MINIMO_MIN, to=config.INTERVALO_MAXIMO_MIN,
                    width=5, textvariable=self.var_intervalo).grid(row=0, column=3, padx=6)
        ttk.Label(controles, text="min").grid(row=0, column=4)

    def _criar_card(self, pai, titulo, cor, coluna):
        quadro = tk.Frame(pai, bg=CARD, highlightbackground=BORDA, highlightthickness=1,
                          padx=18, pady=12)
        quadro.grid(row=0, column=coluna, sticky="nsew", padx=6)
        pai.columnconfigure(coluna, weight=1)
        valor = tk.Label(quadro, text="0", font=(FONTE, 26, "bold"), fg=cor, bg=CARD)
        valor.pack(anchor="w")
        tk.Label(quadro, text=titulo, font=(FONTE, 10), fg=TEXTO_SUAVE, bg=CARD).pack(anchor="w")
        return valor

    def _montar_cards(self):
        area = ttk.Frame(self, padding=(14, 10, 14, 6))
        area.pack(fill="x")
        self.card_encontrados = self._criar_card(area, "Dispositivos encontrados", CIANO, 0)
        self.card_autorizados = self._criar_card(area, "Autorizados", VERDE, 1)
        self.card_desconhecidos = self._criar_card(area, "Desconhecidos", LARANJA, 2)
        self.card_ultima = self._criar_card(area, "Última varredura", TEXTO, 3)
        self.card_ultima.configure(font=(FONTE, 14, "bold"))

    def _criar_tabela(self, pai, colunas):
        """colunas: lista de (id, titulo, largura). Retorna a Treeview."""
        quadro = ttk.Frame(pai)
        quadro.pack(fill="both", expand=True)
        tabela = ttk.Treeview(quadro, columns=[c[0] for c in colunas], show="headings",
                              selectmode="browse")
        for id_col, titulo, largura in colunas:
            tabela.heading(id_col, text=titulo)
            tabela.column(id_col, width=largura, anchor="w")
        barra = ttk.Scrollbar(quadro, orient="vertical", command=tabela.yview)
        tabela.configure(yscrollcommand=barra.set)
        tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        tabela.tag_configure("desconhecido", foreground=LARANJA)
        tabela.tag_configure("autorizado", foreground=VERDE)
        tabela.tag_configure("ativo", foreground=LARANJA)
        tabela.tag_configure("revisado", foreground=TEXTO_SUAVE)
        tabela.tag_configure("resolvido", foreground=TEXTO_SUAVE)
        return tabela

    def _montar_abas(self):
        self.abas = ttk.Notebook(self)
        self.abas.pack(fill="both", expand=True, padx=20, pady=(8, 0))

        # --- Aba Dispositivos
        self.aba_disp = ttk.Frame(self.abas, padding=10)
        self.abas.add(self.aba_disp, text="Dispositivos na rede")
        barra = ttk.Frame(self.aba_disp)
        barra.pack(fill="x", pady=(0, 8))
        ttk.Button(barra, text="✔ Autorizar selecionado", command=self._autorizar_selecionado).pack(side="left")
        self.tab_disp = self._criar_tabela(self.aba_disp, [
            ("status", "Status", 120), ("nome", "Nome", 200), ("ip", "IP", 130),
            ("mac", "MAC Address", 160), ("fabricante", "Fabricante", 220),
        ])

        # --- Aba Alertas
        self.aba_alertas = ttk.Frame(self.abas, padding=10)
        self.abas.add(self.aba_alertas, text="Alertas")
        barra = ttk.Frame(self.aba_alertas)
        barra.pack(fill="x", pady=(0, 8))
        ttk.Button(barra, text="Marcar como revisado", command=self._revisar_alerta).pack(side="left")
        self.tab_alertas = self._criar_tabela(self.aba_alertas, [
            ("data", "Data e hora", 150), ("tipo", "Tipo do evento", 190), ("ip", "IP", 120),
            ("mac", "MAC Address", 150), ("nome", "Nome", 160), ("status", "Status", 90),
        ])

        # --- Aba Autorizados
        self.aba_aut = ttk.Frame(self.abas, padding=10)
        self.abas.add(self.aba_aut, text="Dispositivos autorizados")
        barra = ttk.Frame(self.aba_aut)
        barra.pack(fill="x", pady=(0, 8))
        ttk.Button(barra, text="＋ Adicionar", command=self._adicionar).pack(side="left")
        ttk.Button(barra, text="✎ Editar", command=self._editar).pack(side="left", padx=8)
        ttk.Button(barra, text="🗑 Remover", command=self._remover).pack(side="left")
        self.tab_aut = self._criar_tabela(self.aba_aut, [
            ("nome", "Nome", 200), ("mac", "MAC Address", 160),
            ("descricao", "Descrição", 320), ("criado", "Cadastrado em", 150),
        ])

    def _montar_rodape(self):
        rodape = ttk.Frame(self, padding=(20, 8))
        rodape.pack(fill="x")
        tk.Label(rodape, textvariable=self.var_status, font=(FONTE, 9), fg=TEXTO_SUAVE,
                 bg=FUNDO, anchor="w").pack(side="left")
        tk.Label(rodape, text="Uso exclusivo em redes autorizadas • somente monitoramento",
                 font=(FONTE, 9), fg=BORDA, bg=FUNDO).pack(side="right")

    # ------------------------------------------------------- atualizar a tela
    @staticmethod
    def _preencher(tabela, linhas):
        """linhas: lista de (iid, valores, tag)."""
        tabela.delete(*tabela.get_children())
        for iid, valores, tag in linhas:
            tabela.insert("", "end", iid=iid, values=valores, tags=(tag,))

    @staticmethod
    def _mostrar_mac(mac):
        return "(indisponível)" if mac.startswith("SEM-MAC") else mac

    def atualizar_tudo(self):
        encontrados = dispositivos.listar_encontrados_ultima_varredura()
        total = len(encontrados)
        desconhecidos = sum(1 for d in encontrados if d["status"] == "desconhecido")
        ultima = banco.obter_ultima_varredura()

        self.card_encontrados.config(text=str(total))
        self.card_autorizados.config(text=str(total - desconhecidos))
        self.card_desconhecidos.config(text=str(desconhecidos),
                                       fg=VERMELHO if desconhecidos else LARANJA)
        self.card_ultima.config(text=ultima["data_hora"] if ultima else "Nunca")

        self._preencher(self.tab_disp, [
            (d["mac"],
             (d["status"].upper(),
              d["nome_cadastrado"] or d["nome_host"] or "(sem nome)",
              d["ip"], self._mostrar_mac(d["mac"]), d["fabricante"] or ""),
             d["status"])
            for d in encontrados
        ])

        lista_alertas = alertas.listar_alertas()
        self._preencher(self.tab_alertas, [
            (str(a["id"]),
             (a["data_hora"], "Dispositivo desconhecido", a["ip"] or "",
              self._mostrar_mac(a["mac"] or ""), a["nome_host"] or "(sem nome)",
              a["status"].upper()),
             a["status"])
            for a in lista_alertas
        ])
        ativos = alertas.contar_alertas_ativos()
        self.abas.tab(self.aba_alertas, text=f"Alertas ({ativos})" if ativos else "Alertas")

        self._preencher(self.tab_aut, [
            (a["mac"], (a["nome"], a["mac"], a["descricao"], a["criado_em"]), "autorizado")
            for a in dispositivos.listar_autorizados()
        ])

    # -------------------------------------------------------------- varredura
    def iniciar_varredura(self):
        if self.escaneando:
            return
        self.escaneando = True
        self.botao_varredura.state(["disabled"])
        self.var_status.set("Varrendo a rede… isso pode levar alguns segundos.")

        def trabalho():
            try:
                self.fila.put(("ok", scanner.varrer_rede()))
            except scanner.ErroScanner as erro:
                self.fila.put(("erro", str(erro)))
            except Exception as erro:  # qualquer imprevisto não pode travar a interface
                self.fila.put(("erro", f"Erro inesperado: {erro}"))

        threading.Thread(target=trabalho, daemon=True).start()

    def _verificar_fila(self):
        """Roda a cada 200 ms na thread principal e recebe resultados da varredura."""
        try:
            tipo, dados = self.fila.get_nowait()
        except queue.Empty:
            self.after(200, self._verificar_fila)
            return

        self.escaneando = False
        self.botao_varredura.state(["!disabled"])

        if tipo == "ok":
            rede, lista = dados
            resumo = alertas.processar_varredura(lista, rede)
            self.atualizar_tudo()
            self.var_status.set(
                f"Varredura concluída em {rede}: {resumo['total']} dispositivo(s), "
                f"{resumo['desconhecidos']} desconhecido(s), "
                f"{len(resumo['novos_alertas'])} alerta(s) novo(s)."
            )
            if resumo["novos_alertas"]:
                self._avisar_novos(resumo["novos_alertas"])
        else:
            self.var_status.set("A varredura falhou.")
            messagebox.showerror("NETGUARD", dados)

        if self.var_monitorar.get():
            self._agendar_proxima()
        self.after(200, self._verificar_fila)

    def _avisar_novos(self, novos):
        self.bell()
        self.abas.select(self.aba_alertas)
        linhas = "\n".join(f"• {d['ip']}  {self._mostrar_mac(d['mac'])}  {d['nome'] or ''}" for d in novos[:8])
        extra = f"\n… e mais {len(novos) - 8}" if len(novos) > 8 else ""
        messagebox.showwarning(
            "NETGUARD — dispositivo desconhecido",
            f"{len(novos)} dispositivo(s) desconhecido(s) na rede:\n\n{linhas}{extra}\n\n"
            "Verifique se são seus. Se forem, autorize-os na aba “Dispositivos na rede”.",
        )

    # ------------------------------------------------ monitoramento periódico
    def _ler_intervalo(self):
        try:
            minutos = int(self.var_intervalo.get())
        except ValueError:
            minutos = config.INTERVALO_PADRAO_MIN
        minutos = max(config.INTERVALO_MINIMO_MIN, min(config.INTERVALO_MAXIMO_MIN, minutos))
        self.var_intervalo.set(str(minutos))
        return minutos

    def _cancelar_agendamento(self):
        if self.id_agendamento is not None:
            self.after_cancel(self.id_agendamento)
            self.id_agendamento = None

    def _agendar_proxima(self):
        self._cancelar_agendamento()
        minutos = self._ler_intervalo()
        self.id_agendamento = self.after(minutos * 60 * 1000, self._disparo_automatico)
        self.var_status.set(self.var_status.get() + f"  Próxima em {minutos} min.")

    def _disparo_automatico(self):
        self.id_agendamento = None
        if not self.var_monitorar.get():
            return
        if self.escaneando:  # ainda terminando a anterior: o fim dela reagenda
            return
        self.iniciar_varredura()

    def _alternar_monitoramento(self):
        if self.var_monitorar.get():
            self._ler_intervalo()
            self.iniciar_varredura()  # varre já; ao terminar, agenda a próxima
        else:
            self._cancelar_agendamento()
            self.var_status.set("Monitoramento automático desligado.")

    # ------------------------------------------------------ ações dos botões
    def _selecionado(self, tabela, mensagem="Selecione um item na lista primeiro."):
        selecao = tabela.selection()
        if not selecao:
            messagebox.showinfo("NETGUARD", mensagem)
            return None
        return selecao[0]

    def _autorizar_selecionado(self):
        mac = self._selecionado(self.tab_disp)
        if mac is None:
            return
        if mac.startswith("SEM-MAC"):
            messagebox.showinfo(
                "NETGUARD",
                "O MAC desse dispositivo não foi detectado, então não dá para autorizá-lo.\n\n"
                "Dica: execute o programa como Administrador para o Nmap conseguir ler os MACs.",
            )
            return
        valores = self.tab_disp.item(mac, "values")
        if valores[0] == "AUTORIZADO":
            messagebox.showinfo("NETGUARD", "Esse dispositivo já está autorizado.")
            return
        nome_sugerido = "" if valores[1] == "(sem nome)" else valores[1]

        def salvar(m, n, d):
            dispositivos.adicionar_autorizado(m, n, d)

        DialogoDispositivo(self, "Autorizar dispositivo", salvar, mac=mac,
                           nome=nome_sugerido, mac_editavel=False)
        self.atualizar_tudo()

    def _revisar_alerta(self):
        iid = self._selecionado(self.tab_alertas)
        if iid is None:
            return
        alertas.marcar_como_revisado(int(iid))
        self.atualizar_tudo()

    def _adicionar(self):
        DialogoDispositivo(self, "Adicionar dispositivo autorizado",
                           lambda m, n, d: dispositivos.adicionar_autorizado(m, n, d))
        self.atualizar_tudo()

    def _editar(self):
        mac = self._selecionado(self.tab_aut)
        if mac is None:
            return
        nome, _, descricao, _ = self.tab_aut.item(mac, "values")
        DialogoDispositivo(self, "Editar dispositivo autorizado",
                           lambda m, n, d: dispositivos.editar_autorizado(m, n, d),
                           mac=mac, nome=nome, descricao=descricao, mac_editavel=False)
        self.atualizar_tudo()

    def _remover(self):
        mac = self._selecionado(self.tab_aut)
        if mac is None:
            return
        nome = self.tab_aut.item(mac, "values")[0]
        if messagebox.askyesno("NETGUARD", f"Remover “{nome}” da lista de autorizados?\n\n"
                               "Se ele estiver na rede, voltará a ser desconhecido."):
            dispositivos.remover_autorizado(mac)
            self.atualizar_tudo()
