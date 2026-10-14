"""Analisador sintatico da linguagem de receitas (E3).

Uso:
    python src/sintatico.py caminho/do/programa.rc
    python src/sintatico.py caminho/do/programa.rc --tree
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from antlr4 import CommonTokenStream, FileStream
from antlr4.error.ErrorListener import ErrorListener
from antlr4.tree.Trees import Trees

from gerado.ReceitaLexer import ReceitaLexer
from gerado.ReceitaParser import ReceitaParser


class OuvinteErrosSintaticos(ErrorListener):
    def __init__(self):
        super().__init__()
        self.erros = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        texto = offendingSymbol.text if offendingSymbol else "?"
        self.erros.append({
            "linha": line,
            "coluna": column + 1,
            "simbolo": texto,
            "msg_original": msg,
        })


def formatar_erro_sintatico(erro, caminho):
    msg = erro["msg_original"]
    simbolo = erro["simbolo"]

    # Traduz mensagens padrao do ANTLR para mensagens claras em portugues
    if "missing ';'" in msg.lower() or "missing PONTOVIRG" in msg:
        desc = "faltou ';' no final da instrucao"
    elif "missing ':'" in msg.lower() or "missing DOISPONTOS" in msg:
        desc = "faltou ':' apos a declaracao do passo"
    elif "missing ')'" in msg.lower() or "missing FECHAPAR" in msg:
        desc = "faltou ')' para fechar a expressao"
    elif "mismatched input" in msg.lower():
        desc = f"simbolo inesperado {simbolo!r}"
    elif "no viable alternative" in msg.lower():
        desc = f"estrutura sintatica invalida proximo a {simbolo!r}"
    elif "extraneous input" in msg.lower():
        desc = f"conteudo a mais ou fora de ordem proximo a {simbolo!r}"
    else:
        desc = f"erro proximo a {simbolo!r} ({msg})"

    return f"ERRO sintatico: {desc} em {caminho}, linha {erro['linha']}, coluna {erro['coluna']}"


def imprimir_arvore_indentada(no, parser, nivel=0):
    """Imprime a arvore sintatica formatada com indentacao."""
    regra_nomes = parser.ruleNames
    if hasattr(no, "getRuleIndex"):
        nome_regra = regra_nomes[no.getRuleIndex()]
        print("  " * nivel + f"({nome_regra}")
        for i in range(no.getChildCount()):
            imprimir_arvore_indentada(no.getChild(i), parser, nivel + 1)
        print("  " * nivel + ")")
    else:
        texto = no.getText()
        if texto != "<EOF>":
            print("  " * nivel + f"'{texto}'")


def main():
    if len(sys.argv) < 2:
        print("uso: python src/sintatico.py <arquivo> [--tree]", file=sys.stderr)
        return 2

    caminho = sys.argv[1]
    mostrar_arvore = "--tree" in sys.argv

    if not os.path.isfile(caminho):
        print(f"Erro: arquivo '{caminho}' nao encontrado.", file=sys.stderr)
        return 2

    # 1. Analise Lexica
    entrada = FileStream(caminho, encoding="utf-8")
    lexer = ReceitaLexer(entrada)
    ouvinte_lexer = OuvinteErrosSintaticos()
    lexer.removeErrorListeners()
    lexer.addErrorListener(ouvinte_lexer)

    # 2. Analise Sintatica
    tokens = CommonTokenStream(lexer)
    parser = ReceitaParser(tokens)
    ouvinte_parser = OuvinteErrosSintaticos()
    parser.removeErrorListeners()
    parser.addErrorListener(ouvinte_parser)

    # Dispara a analise a partir da regra inicial (programa)
    arvore = parser.programa()

    erros = ouvinte_lexer.erros + ouvinte_parser.erros
    if erros:
        for erro in erros:
            print(formatar_erro_sintatico(erro, caminho), file=sys.stderr)
        return 1

    print(f"OK sintatico: '{caminho}' compilado com sucesso sem erros de sintaxe.")
    if mostrar_arvore:
        print("\n--- Arvore Sintatica (S-Expression) ---")
        print(Trees.toStringTree(arvore, None, parser))
        print("\n--- Arvore Sintatica Indentada ---")
        imprimir_arvore_indentada(arvore, parser)

    return 0


if __name__ == "__main__":
    sys.exit(main())
