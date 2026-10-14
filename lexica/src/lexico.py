"""Analisador lexico da linguagem de receitas.

Uso: python src/lexico.py caminho/do/programa.rc
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from antlr4 import FileStream, Token
from antlr4.error.ErrorListener import ErrorListener

from gerado.ReceitaLexer import ReceitaLexer


class ErroLexico(ErrorListener):
    def __init__(self):
        self.erros = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.erros.append((line, column + 1, msg))


def main():
    if len(sys.argv) != 2:
        print("uso: python src/lexico.py <arquivo>", file=sys.stderr)
        return 2

    caminho = sys.argv[1]
    lexer = ReceitaLexer(FileStream(caminho, encoding="utf-8"))
    erros = ErroLexico()
    lexer.removeErrorListeners()
    lexer.addErrorListener(erros)

    nomes = lexer.symbolicNames
    total = 0
    while True:
        tok = lexer.nextToken()
        if tok.type == Token.EOF:
            break
        print(f"{nomes[tok.type]} {tok.text!r} linha {tok.line}")
        total += 1

    print(f"{total} tokens reconhecidos")

    for linha, coluna, msg in erros.erros:
        # msg do ANTLR: "token recognition error at: '<texto>'"
        trecho = msg.split("at: ", 1)[-1].strip("'")
        if trecho.startswith('"'):
            desc = "texto sem fechar (faltou a aspa de fechamento)"
        elif trecho.startswith("."):
            desc = "numero malformado (ponto sem digito antes/depois)"
        else:
            desc = f"caractere invalido {trecho[:1]!r}"
        print(f"ERRO lexico: {desc} em {caminho}, linha {linha}, coluna {coluna}",
              file=sys.stderr)
    return 1 if erros.erros else 0


if __name__ == "__main__":
    sys.exit(main())
