"""Analisador sintatico da linguagem de receitas (E3).

Uso:
    python src/sintatico.py caminho/do/programa.rc
    python src/sintatico.py caminho/do/programa.rc --tree
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from antlr4 import CommonTokenStream, FileStream, Token
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.ErrorStrategy import DefaultErrorStrategy
from antlr4.error.Errors import InputMismatchException
from antlr4.tree.Trees import Trees

from gerado.ReceitaLexer import ReceitaLexer
from gerado.ReceitaParser import ReceitaParser


# Nomes amigaveis para os tokens que nao tem um texto fixo
NOMES = {
    Token.EOF: "fim do arquivo",
    ReceitaParser.PASSO: "'passo N'",
    ReceitaParser.ACAO: "uma acao (misture, asse...)",
    ReceitaParser.PREPOSICAO: "uma preposicao (em, por, a, ate, com)",
    ReceitaParser.UNIDADE: "uma unidade (g, kg, ml, xicara...)",
    ReceitaParser.TEMPO: "um tempo (seg, min, h)",
    ReceitaParser.NUMERO: "um numero",
    ReceitaParser.TEXTO: "um texto",
    ReceitaParser.IDENT: "um nome",
}


def nome_token(tipo):
    if tipo in NOMES:
        return NOMES[tipo]
    return ReceitaParser.literalNames[tipo]


def texto_encontrado(token):
    if token.type == Token.EOF:
        return "fim do arquivo"
    return f"'{token.text}'"


class ModoPanico(DefaultErrorStrategy):
    """Recuperacao em modo panico: depois de um erro, joga fora tudo ate um
    ponto seguro (';' ou 'passo N') e recomeca dali, sem gerar mensagens
    fantasmas para os tokens descartados."""

    SINCRONIZA = {ReceitaParser.PONTOVIRG, ReceitaParser.PASSO, Token.EOF}

    # Regras que ficam dentro de um comando: param ANTES do ';',
    # para o proprio comando consumir o ';' dele
    DENTRO_DO_COMANDO = {
        ReceitaParser.RULE_expr,
        ReceitaParser.RULE_lista_argumentos,
        ReceitaParser.RULE_argumento,
        ReceitaParser.RULE_modificador,
        ReceitaParser.RULE_complemento,
    }

    def sincroniza(self, parser):
        while parser.getTokenStream().LA(1) not in self.SINCRONIZA:
            parser.consume()
        if parser.getTokenStream().LA(1) == ReceitaParser.PONTOVIRG and \
                parser._ctx.getRuleIndex() not in self.DENTRO_DO_COMANDO:
            parser.consume()

    def recover(self, parser, e):
        self.sincroniza(parser)

    def sync(self, parser):
        # Chamado pelo ANTLR antes de cada laco/opcao da gramatica
        if self.inErrorRecoveryMode(parser):
            return
        if parser.getTokenStream().LA(1) in parser.getExpectedTokens():
            return
        self.reporta(parser, parser.getCurrentToken(), parser.getExpectedTokens())
        if parser._ctx.getRuleIndex() in (ReceitaParser.RULE_programa, ReceitaParser.RULE_bloco_passo):
            # Laco de comandos: descarta o comando errado e continua no laco
            self.sincroniza(parser)
        else:
            # Dentro de um comando: sai da regra e o recover() sincroniza
            raise InputMismatchException(parser)

    # Toda mensagem tem: onde (linha e coluna), o que esperava e o que encontrou
    def reporta(self, parser, token, esperados):
        if self.inErrorRecoveryMode(parser):
            return
        self.beginErrorCondition(parser)
        # "fim do arquivo" (EOF = -1) vai por ultimo na lista
        tipos = sorted(esperados, key=lambda t: t == Token.EOF)
        nomes = [nome_token(t) for t in tipos]
        if len(nomes) > 1:
            esperava = ", ".join(nomes[:-1]) + " ou " + nomes[-1]
        else:
            esperava = nomes[0]
        parser.notifyErrorListeners(f"esperava {esperava}, encontrou {texto_encontrado(token)}", token, None)

    def reportError(self, parser, e):
        self.reporta(parser, e.offendingToken, e.getExpectedTokens())

    def reportMissingToken(self, parser):
        self.reporta(parser, parser.getCurrentToken(), parser.getExpectedTokens())

    def reportUnwantedToken(self, parser):
        self.reporta(parser, parser.getCurrentToken(), parser.getExpectedTokens())


class OuvinteErros(ErrorListener):
    def __init__(self):
        super().__init__()
        self.erros = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        if isinstance(recognizer, ReceitaLexer):
            # O lexer avisa "token recognition error at: '?'"
            msg = "caractere invalido " + msg.split("at: ")[-1]
        self.erros.append((line, column + 1, msg))


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
    ouvinte_lexer = OuvinteErros()
    lexer.removeErrorListeners()
    lexer.addErrorListener(ouvinte_lexer)

    # 2. Analise Sintatica
    tokens = CommonTokenStream(lexer)
    parser = ReceitaParser(tokens)
    ouvinte_parser = OuvinteErros()
    parser.removeErrorListeners()
    parser.addErrorListener(ouvinte_parser)
    parser._errHandler = ModoPanico()

    # Dispara a analise a partir da regra inicial (programa)
    arvore = parser.programa()

    erros = ouvinte_lexer.erros + ouvinte_parser.erros
    if erros:
        for linha, coluna, msg in sorted(erros):
            print(f"ERRO sintatico em {caminho}, linha {linha}, coluna {coluna}: {msg}", file=sys.stderr)
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
