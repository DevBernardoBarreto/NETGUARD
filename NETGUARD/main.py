"""main.py - Ponto de entrada do NETGUARD. Execute: python main.py"""
import banco
from interface import NetGuardApp


def main():
    banco.criar_tabelas()
    app = NetGuardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
