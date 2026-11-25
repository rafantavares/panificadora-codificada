"""Analisador semantico e construtor da AST da linguagem de receitas (E4 / E5).

Implementa:
1. Construcao da Arvore Sintatica Abstrata (AST) via ReceitaVisitor (Aula 14),
   eliminando nos de andaime da gramatica e pontuacao (';', ':', '=', '(', ')', ',').
2. Pilha de Tabelas de Simbolos com suporte a escopo global e escopos locais por
   bloco de passo ('empilhar', 'desempilhar', 'declarar' no topo e 'buscar' do
   topo para a base, permitindo sombreamento entre escopos distintos).
3. Verificacao semantica e de tipos (atributos sintetizados bottom-up):
   - Uso de ingrediente ou variavel nao declarada em expressoes e acoes.
   - Declaracao duplicada de ingrediente no mesmo escopo.
   - Inferencia de tipos ('inteiro', 'real', 'texto') com coercao sem perda
     ('inteiro' -> 'real') e anotacao de 'tipo_inferido' nos nos da AST.
   - Incompatibilidade de tipos (ex.: atribuir 'real' a 'inteiro' com perda de
     precisao, 'porcoes' nao inteiro, ou somar ingredientes de dimensoes fisicas
     incompativeis como massa 'g/kg' com volume 'ml/l') e divisao por zero.

Uso:
    python src/semantico.py caminho/do/programa.rc
    python src/semantico.py caminho/do/programa.rc --ast
    python src/semantico.py caminho/do/programa.rc --tabela
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from antlr4 import CommonTokenStream, FileStream, Token
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.ErrorStrategy import DefaultErrorStrategy
from antlr4.error.Errors import InputMismatchException

from gerado.ReceitaLexer import ReceitaLexer
from gerado.ReceitaParser import ReceitaParser
from gerado.ReceitaVisitor import ReceitaVisitor


# ============================================================================
# 1. RECUPERACAO DE ERROS SINTATICOS (MODO PANICO - E3)
# ============================================================================

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
    """Recuperacao em modo panico herdada da etapa sintatica (E3)."""

    SINCRONIZA = {ReceitaParser.PONTOVIRG, ReceitaParser.PASSO, Token.EOF}

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
        if self.inErrorRecoveryMode(parser):
            return
        if parser.getTokenStream().LA(1) in parser.getExpectedTokens():
            return
        self.reporta(parser, parser.getCurrentToken(), parser.getExpectedTokens())
        if parser._ctx.getRuleIndex() in (ReceitaParser.RULE_programa, ReceitaParser.RULE_bloco_passo):
            self.sincroniza(parser)
        else:
            raise InputMismatchException(parser)

    def reporta(self, parser, token, esperados):
        if self.inErrorRecoveryMode(parser):
            return
        self.beginErrorCondition(parser)
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
            msg = "caractere invalido " + msg.split("at: ")[-1]
        self.erros.append((line, column + 1, msg))


# ============================================================================
# 2. NOS DA ARVORE SINTATICA ABSTRATA (AST) E VISITOR (AULA 14)
# ============================================================================

class No:
    """No da Arvore Sintatica Abstrata (AST).

    Guarda apenas os conceitos da linguagem (Programa, Receita, Porcoes,
    Declara, Atribui, Passo, Acao, Modificador, Op, Num, Texto, Var),
    a posicao no codigo-fonte (linha e coluna) para mensagens de erro
    semantico e o atributo sintetizado 'tipo_inferido'.
    """

    def __init__(self, classe, linha=0, coluna=0, **campos):
        self.classe = classe
        self.linha = linha
        self.coluna = coluna
        self.campos = campos
        self.tipo_inferido = None
        self.dimensao_inferida = None

    def __getattr__(self, nome):
        if "campos" in self.__dict__ and nome in self.campos:
            return self.campos[nome]
        raise AttributeError(f"No '{self.classe}' nao possui campo '{nome}'")

    def __repr__(self):
        partes = [f"{k}={v!r}" for k, v in self.campos.items()]
        if self.tipo_inferido:
            partes.append(f"tipo={self.tipo_inferido}")
        return f"{self.classe}({', '.join(partes)})"


def contar_nos_parse(arvore):
    """Conta o total de nos (regras + folhas) da Arvore de Parse do ANTLR."""
    if not hasattr(arvore, "getChildCount"):
        return 1
    total = 1
    for i in range(arvore.getChildCount()):
        total += contar_nos_parse(arvore.getChild(i))
    return total


def contar_nos_ast(no):
    """Conta o total de nos da AST enxuta."""
    if isinstance(no, No):
        total = 1
        for valor in no.campos.values():
            total += contar_nos_ast(valor)
        return total
    if isinstance(no, list):
        return sum(contar_nos_ast(item) for item in no)
    return 0


def imprimir_ast(no, nivel=0):
    """Imprime a AST indentada com as anotacoes de tipo inferido."""
    recuo = "  " * nivel
    if not isinstance(no, No):
        print(f"{recuo}{no!r}")
        return

    anotacao_tipo = f"  [tipo: {no.tipo_inferido}]" if no.tipo_inferido else ""
    coercao = f"  (coercao: {no.campos['coercao']})" if "coercao" in no.campos else ""
    simples = []
    filhos = []

    for chave, valor in no.campos.items():
        if chave == "coercao":
            continue
        if isinstance(valor, No) or (isinstance(valor, list) and any(isinstance(x, No) for x in valor)):
            filhos.append((chave, valor))
        else:
            simples.append(f"{chave}={valor!r}")

    resumo = ", ".join(simples)
    cabecalho = f"{recuo}{no.classe}({resumo}){anotacao_tipo}{coercao}"
    print(cabecalho)

    for chave, valor in filhos:
        if isinstance(valor, list):
            for item in valor:
                imprimir_ast(item, nivel + 1)
        else:
            imprimir_ast(valor, nivel + 1)


class ConstrutorAST(ReceitaVisitor):
    """Converte a Arvore de Parse do ANTLR em uma AST enxuta (Aula 14).

    Descarta nos intermediarios de andaime (declaracao_global, comando_passo,
    lista_argumentos, argumento, complemento) e tokens de pontuacao (';', ':',
    '=', '(', ')', ',').
    """

    def _pos(self, token):
        return token.line, token.column + 1

    # programa : declaracao_receita? declaracao_porcoes? declaracao_global* bloco_passo* EOF ;
    def visitPrograma(self, ctx: ReceitaParser.ProgramaContext):
        receita = self.visit(ctx.declaracao_receita()) if ctx.declaracao_receita() else None
        porcoes = self.visit(ctx.declaracao_porcoes()) if ctx.declaracao_porcoes() else None
        declaracoes = [self.visit(d) for d in ctx.declaracao_global()]
        passos = [self.visit(p) for p in ctx.bloco_passo()]
        linha, coluna = self._pos(ctx.start)
        return No(
            "Programa",
            linha=linha,
            coluna=coluna,
            receita=receita,
            porcoes=porcoes,
            declaracoes=declaracoes,
            passos=passos,
        )

    # declaracao_receita : RECEITA TEXTO PONTOVIRG ;
    def visitDeclaracao_receita(self, ctx: ReceitaParser.Declaracao_receitaContext):
        tok = ctx.TEXTO().getSymbol()
        linha, coluna = self._pos(tok)
        return No("Receita", linha=linha, coluna=coluna, nome=tok.text[1:-1])

    # declaracao_porcoes : PORCOES NUMERO PONTOVIRG ;
    def visitDeclaracao_porcoes(self, ctx: ReceitaParser.Declaracao_porcoesContext):
        tok = ctx.NUMERO().getSymbol()
        linha, coluna = self._pos(tok)
        texto = tok.text
        valor = float(texto) if "." in texto else int(texto)
        no_num = No("Num", linha=linha, coluna=coluna, valor=valor)
        return No("Porcoes", linha=linha, coluna=coluna, qtd=no_num)

    # Regra de repasse com 1 filho (Aula 14, slide 16):
    # if ctx.getChildCount() == 1: return self.visit(ctx.getChild(0))
    def visitDeclaracao_global(self, ctx: ReceitaParser.Declaracao_globalContext):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))
        return self.visitChildren(ctx)

    # declaracao_ingrediente : INGREDIENTE IDENT expr UNIDADE PONTOVIRG ;
    def visitDeclaracao_ingrediente(self, ctx: ReceitaParser.Declaracao_ingredienteContext):
        tok_id = ctx.IDENT().getSymbol()
        linha, coluna = self._pos(tok_id)
        return No(
            "Declara",
            linha=linha,
            coluna=coluna,
            nome=tok_id.text,
            qtd=self.visit(ctx.expr()),
            unidade=ctx.UNIDADE().getText(),
        )

    # atribuicao : IDENT IGUAL expr PONTOVIRG ;
    def visitAtribuicao(self, ctx: ReceitaParser.AtribuicaoContext):
        tok_id = ctx.IDENT().getSymbol()
        linha, coluna = self._pos(tok_id)
        return No(
            "Atribui",
            linha=linha,
            coluna=coluna,
            alvo=tok_id.text,
            valor=self.visit(ctx.expr()),
        )

    # bloco_passo : PASSO DOISPONTOS comando_passo* ;
    def visitBloco_passo(self, ctx: ReceitaParser.Bloco_passoContext):
        tok_passo = ctx.PASSO().getSymbol()
        linha, coluna = self._pos(tok_passo)
        sufixo = tok_passo.text[5:].strip()
        numero = int(sufixo) if sufixo.isdigit() else tok_passo.text
        comandos = [self.visit(c) for c in ctx.comando_passo()]
        return No("Passo", linha=linha, coluna=coluna, numero=numero, comandos=comandos)

    # Regra de repasse com 1 filho (Aula 14, slide 16)
    def visitComando_passo(self, ctx: ReceitaParser.Comando_passoContext):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))
        return self.visitChildren(ctx)

    # comando_acao : ACAO lista_argumentos? modificador* PONTOVIRG ;
    def visitComando_acao(self, ctx: ReceitaParser.Comando_acaoContext):
        tok_acao = ctx.ACAO().getSymbol()
        linha, coluna = self._pos(tok_acao)
        argumentos = self.visit(ctx.lista_argumentos()) if ctx.lista_argumentos() else []
        modificadores = [self.visit(m) for m in ctx.modificador()]
        return No(
            "Acao",
            linha=linha,
            coluna=coluna,
            verbo=tok_acao.text,
            argumentos=argumentos,
            modificadores=modificadores,
        )

    # lista_argumentos : argumento (VIRGULA argumento)* ;
    def visitLista_argumentos(self, ctx: ReceitaParser.Lista_argumentosContext):
        return [self.visit(a) for a in ctx.argumento()]

    # argumento : IDENT | TEXTO ;
    def visitArgumento(self, ctx: ReceitaParser.ArgumentoContext):
        if ctx.IDENT():
            tok = ctx.IDENT().getSymbol()
            linha, coluna = self._pos(tok)
            return No("Var", linha=linha, coluna=coluna, nome=tok.text)
        tok = ctx.TEXTO().getSymbol()
        linha, coluna = self._pos(tok)
        return No("Texto", linha=linha, coluna=coluna, valor=tok.text[1:-1])

    # modificador : PREPOSICAO complemento ;
    def visitModificador(self, ctx: ReceitaParser.ModificadorContext):
        tok_prep = ctx.PREPOSICAO().getSymbol()
        linha, coluna = self._pos(tok_prep)
        comp = self.visit(ctx.complemento())
        return No(
            "Modificador",
            linha=linha,
            coluna=coluna,
            preposicao=tok_prep.text,
            **comp,
        )

    # complemento : expr (TEMPO | TEMPERATURA)? | IDENT | TEXTO ;
    def visitComplemento(self, ctx: ReceitaParser.ComplementoContext):
        if ctx.expr():
            medida = None
            if ctx.TEMPO():
                medida = ctx.TEMPO().getText()
            elif ctx.TEMPERATURA():
                medida = ctx.TEMPERATURA().getText()
            return {"valor": self.visit(ctx.expr()), "medida": medida}
        if ctx.TEXTO():
            tok = ctx.TEXTO().getSymbol()
            linha, coluna = self._pos(tok)
            return {"valor": No("Texto", linha=linha, coluna=coluna, valor=tok.text[1:-1]), "medida": None}
        tok = ctx.IDENT().getSymbol()
        linha, coluna = self._pos(tok)
        return {"valor": No("Var", linha=linha, coluna=coluna, nome=tok.text), "medida": None}

    # expr : ABREPAR expr FECHAPAR
    #      | expr (VEZES | DIV) expr
    #      | expr (MAIS | MENOS) expr
    #      | NUMERO
    #      | IDENT ;
    def visitExpr(self, ctx: ReceitaParser.ExprContext):
        # Folha: NUMERO ou IDENT
        if ctx.NUMERO():
            tok = ctx.NUMERO().getSymbol()
            linha, coluna = self._pos(tok)
            texto = tok.text
            valor = float(texto) if "." in texto else int(texto)
            return No("Num", linha=linha, coluna=coluna, valor=valor)

        if ctx.IDENT():
            tok = ctx.IDENT().getSymbol()
            linha, coluna = self._pos(tok)
            return No("Var", linha=linha, coluna=coluna, nome=tok.text)

        # Parenteses: ( expr ) -> retorna a subarvore interna sem criar no 'Paren'
        if ctx.ABREPAR():
            return self.visit(ctx.expr(0))

        # Operacao binaria: esq op dir (Aula 14, slide 16)
        tok_op = ctx.getChild(1).getSymbol()
        linha, coluna = self._pos(tok_op)
        return No(
            "Op",
            linha=linha,
            coluna=coluna,
            op=tok_op.text,
            esq=self.visit(ctx.expr(0)),
            dir=self.visit(ctx.expr(1)),
        )


# ============================================================================
# 3. TABELA DE SIMBOLOS E PILHA DE ESCOPOS (AULA 14 / RESUMAO G2)
# ============================================================================

DIMENSAO_UNIDADE = {
    "g": "massa",
    "kg": "massa",
    "ml": "volume",
    "l": "volume",
    "xicara": "medida",
    "colher": "medida",
    "pitada": "medida",
    "un": "contagem",
}


class Simbolo:
    """Entrada da Tabela de Simbolos."""

    def __init__(self, nome, categoria, tipo, unidade=None, linha=0, coluna=0, escopo="global"):
        self.nome = nome
        self.categoria = categoria  # 'ingrediente' ou 'variavel'
        self.tipo = tipo            # 'inteiro', 'real' ou 'texto'
        self.unidade = unidade      # 'g', 'ml', 'xicara', etc. (None para variaveis)
        self.dimensao = DIMENSAO_UNIDADE.get(unidade) if unidade else None
        self.linha = linha
        self.coluna = coluna
        self.escopo = escopo

    def __repr__(self):
        un = f", unidade={self.unidade!r}" if self.unidade else ""
        return f"Simbolo(nome={self.nome!r}, cat={self.categoria!r}, tipo={self.tipo!r}{un}, linha={self.linha})"


class PilhaTabelas:
    """Pilha de Tabelas de Simbolos para controle de escopos (Aula 14, slide 21).

    - escopo global na base da pilha (`pilha[0]`).
    - cada `passo N:` empilha um novo escopo local e o desempilha ao terminar.
    - `declarar(nome, simbolo)` verifica APENAS o escopo do topo:
      "este nome ja existe neste escopo?"
    - `buscar(nome)` percorre do topo para a base (`reversed(self.pilha)`),
      permitindo sombreamento (shadowing) entre escopos distintos.
    """

    def __init__(self):
        self.pilha = [{}]
        self.nomes_escopos = ["global"]
        self.historico = [("global", self.pilha[0])]

    @property
    def escopo_atual(self):
        return self.nomes_escopos[-1]

    def empilhar(self, nome_escopo):
        novo = {}
        self.pilha.append(novo)
        self.nomes_escopos.append(nome_escopo)
        self.historico.append((nome_escopo, novo))

    def desempilhar(self):
        if len(self.pilha) > 1:
            self.pilha.pop()
            self.nomes_escopos.pop()

    def buscar_no_topo(self, nome):
        return self.pilha[-1].get(nome)

    def declarar(self, nome, simbolo):
        if nome in self.pilha[-1]:
            return False
        self.pilha[-1][nome] = simbolo
        return True

    def buscar(self, nome):
        for escopo in reversed(self.pilha):
            if nome in escopo:
                return escopo[nome]
        return None


def imprimir_tabela_simbolos(pilha_tabelas):
    """Imprime todos os escopos e simbolos registrados durante a analise."""
    print(f"{'ESCOPO':<12} | {'NOME':<16} | {'CATEGORIA':<12} | {'TIPO':<10} | {'UNIDADE':<10} | {'LINHA':<5}")
    print("-" * 78)
    for nome_escopo, tabela in pilha_tabelas.historico:
        for simb in tabela.values():
            unidade = simb.unidade if simb.unidade else "-"
            print(
                f"{nome_escopo:<12} | {simb.nome:<16} | {simb.categoria:<12} | "
                f"{simb.tipo:<10} | {unidade:<10} | {simb.linha:<5}"
            )


# ============================================================================
# 4. ANALISADOR SEMANTICO E VERIFICACAO DE TIPOS (ENCONTROS 14-16)
# ============================================================================

# Utensilios culinarios aceitos em 'unte <utensilio>' e na preposicao 'em <utensilio>'
UTENSILIOS_CULINARIOS = {
    "forma",
    "assadeira",
    "panela",
    "tigela",
    "vasilha",
    "tabuleiro",
    "frigideira",
    "forno",
    "liquidificador",
    "batedeira",
}


class AnalisadorSemantico:
    """Percorre a AST realizando verificacao de escopo, declaracoes e tipos."""

    def __init__(self):
        self.tabelas = PilhaTabelas()
        self.erros = []

    def erro(self, linha, coluna, msg):
        self.erros.append((linha, coluna, msg))

    def analisar(self, ast):
        self.visitar_programa(ast)
        return self.erros

    def visitar_programa(self, no):
        if no.receita is not None:
            no.receita.tipo_inferido = "texto"

        if no.porcoes is not None:
            self.visitar_porcoes(no.porcoes)

        for decl in no.declaracoes:
            if decl.classe == "Declara":
                self.visitar_declara(decl)
            elif decl.classe == "Atribui":
                self.visitar_atribui(decl)

        passos_vistos = {}
        for passo in no.passos:
            if passo.numero in passos_vistos:
                linha_ant = passos_vistos[passo.numero]
                self.erro(
                    passo.linha,
                    passo.coluna,
                    f"'passo {passo.numero}' duplicado (ja definido na linha {linha_ant})",
                )
            else:
                passos_vistos[passo.numero] = passo.linha
            self.visitar_passo(passo)

    def visitar_porcoes(self, no):
        tipo_qtd = self.inferir_tipo_expr(no.qtd)
        no.tipo_inferido = tipo_qtd
        if tipo_qtd != "inteiro":
            self.erro(
                no.qtd.linha,
                no.qtd.coluna,
                f"tipos incompativeis em 'porcoes': quantidade de porcoes deve ser do tipo 'inteiro', encontrou '{tipo_qtd}'",
            )
        elif no.qtd.classe == "Num" and no.qtd.valor <= 0:
            self.erro(
                no.qtd.linha,
                no.qtd.coluna,
                f"quantidade invalida em 'porcoes': valor deve ser maior que zero, encontrou {no.qtd.valor}",
            )

    def visitar_declara(self, no):
        tipo_qtd = self.inferir_tipo_expr(no.qtd)
        no.tipo_inferido = tipo_qtd
        no.dimensao_inferida = DIMENSAO_UNIDADE.get(no.unidade)

        if no.qtd.classe == "Num" and no.qtd.valor <= 0:
            self.erro(
                no.qtd.linha,
                no.qtd.coluna,
                f"quantidade invalida para o ingrediente '{no.nome}': valor deve ser maior que zero, encontrou {no.qtd.valor}",
            )

        existente = self.tabelas.buscar_no_topo(no.nome)
        if existente is not None:
            self.erro(
                no.linha,
                no.coluna,
                f"ingrediente '{no.nome}' declarado duas vezes no mesmo escopo (ja declarado na linha {existente.linha})",
            )
            return

        simbolo = Simbolo(
            nome=no.nome,
            categoria="ingrediente",
            tipo=tipo_qtd if tipo_qtd in ("inteiro", "real") else "real",
            unidade=no.unidade,
            linha=no.linha,
            coluna=no.coluna,
            escopo=self.tabelas.escopo_atual,
        )
        self.tabelas.declarar(no.nome, simbolo)

    def visitar_atribui(self, no):
        # 1. Avalia primeiro a expressao do lado direito (atributos sintetizados)
        tipo_valor = self.inferir_tipo_expr(no.valor)
        no.tipo_inferido = tipo_valor
        no.dimensao_inferida = no.valor.dimensao_inferida

        # 2. Verifica o identificador do lado esquerdo no escopo atual
        existente_topo = self.tabelas.buscar_no_topo(no.alvo)
        if existente_topo is not None:
            if tipo_valor != "erro" and not self.tipos_compativeis_atribuicao(existente_topo.tipo, tipo_valor):
                self.erro(
                    no.linha,
                    no.coluna,
                    f"tipos incompativeis na atribuicao a '{no.alvo}': nao e possivel atribuir '{tipo_valor}' a '{existente_topo.tipo}' sem perda de precisao",
                )
            elif existente_topo.tipo == "real" and tipo_valor == "inteiro":
                no.campos["coercao"] = "inteiro -> real"
                no.tipo_inferido = "real"
            return

        # Se nao existe no escopo do topo, registra na tabela do escopo atual
        # (permite sombreamento caso exista em escopo externo, conforme Aula 14 slide 21)
        tipo_simbolo = tipo_valor if tipo_valor != "erro" else "real"
        simbolo = Simbolo(
            nome=no.alvo,
            categoria="variavel",
            tipo=tipo_simbolo,
            unidade=None,
            linha=no.linha,
            coluna=no.coluna,
            escopo=self.tabelas.escopo_atual,
        )
        simbolo.dimensao = no.dimensao_inferida
        self.tabelas.declarar(no.alvo, simbolo)

    def visitar_passo(self, no):
        # Cada bloco 'passo N:' abre um novo escopo na pilha de tabelas
        self.tabelas.empilhar(f"passo {no.numero}")
        for cmd in no.comandos:
            if cmd.classe == "Acao":
                self.visitar_acao(cmd)
            elif cmd.classe == "Atribui":
                self.visitar_atribui(cmd)
        self.tabelas.desempilhar()

    def visitar_acao(self, no):
        for arg in no.argumentos:
            if arg.classe == "Var":
                # 'unte forma;' permite utensilios culinarios conhecidos
                if no.verbo == "unte" and arg.nome in UTENSILIOS_CULINARIOS:
                    arg.tipo_inferido = "utensilio"
                    continue
                simb = self.tabelas.buscar(arg.nome)
                if simb is None:
                    self.erro(
                        arg.linha,
                        arg.coluna,
                        f"ingrediente '{arg.nome}' usado em '{no.verbo}' sem ter sido declarado",
                    )
                else:
                    arg.tipo_inferido = simb.tipo
            elif arg.classe == "Texto":
                arg.tipo_inferido = "texto"

        for mod in no.modificadores:
            self.visitar_modificador(mod)

    def visitar_modificador(self, no):
        valor = no.valor
        medida = no.medida

        if medida is not None:
            # Complemento com medida: expr (TEMPO | TEMPERATURA)
            tipo_val = self.inferir_tipo_expr(valor)
            no.tipo_inferido = tipo_val
        else:
            # Complemento sem medida: TEXTO, IDENT ou expr pura
            if valor.classe == "Texto":
                valor.tipo_inferido = "texto"
                no.tipo_inferido = "texto"
            elif valor.classe == "Var":
                if no.preposicao == "em" and valor.nome in UTENSILIOS_CULINARIOS:
                    valor.tipo_inferido = "utensilio"
                    no.tipo_inferido = "utensilio"
                else:
                    simb = self.tabelas.buscar(valor.nome)
                    if simb is None:
                        self.erro(
                            valor.linha,
                            valor.coluna,
                            f"ingrediente '{valor.nome}' usado apos '{no.preposicao}' sem ter sido declarado",
                        )
                    else:
                        valor.tipo_inferido = simb.tipo
                        no.tipo_inferido = simb.tipo
            else:
                no.tipo_inferido = self.inferir_tipo_expr(valor)

    def tipos_compativeis_atribuicao(self, tipo_alvo, tipo_valor):
        if tipo_alvo == tipo_valor:
            return True
        # Coercao sem perda: inteiro pode ser atribuido a real
        if tipo_alvo == "real" and tipo_valor == "inteiro":
            return True
        return False

    def inferir_tipo_expr(self, no):
        """Inferencia de tipos bottom-up (atributos sintetizados - Aula 14)."""
        if no.classe == "Num":
            no.tipo_inferido = "real" if isinstance(no.valor, float) else "inteiro"
            no.dimensao_inferida = None
            return no.tipo_inferido

        if no.classe == "Texto":
            no.tipo_inferido = "texto"
            no.dimensao_inferida = None
            return "texto"

        if no.classe == "Var":
            simb = self.tabelas.buscar(no.nome)
            if simb is None:
                self.erro(
                    no.linha,
                    no.coluna,
                    f"variavel ou ingrediente '{no.nome}' usado em expressao sem ter sido declarado",
                )
                no.tipo_inferido = "erro"
                no.dimensao_inferida = None
                return "erro"
            no.tipo_inferido = simb.tipo
            no.dimensao_inferida = simb.dimensao
            return simb.tipo

        if no.classe == "Op":
            t_esq = self.inferir_tipo_expr(no.esq)
            t_dir = self.inferir_tipo_expr(no.dir)

            if "erro" in (t_esq, t_dir):
                no.tipo_inferido = "erro"
                return "erro"

            # Verificacao de compatibilidade dimensional em soma/subtracao de ingredientes
            dim_esq = no.esq.dimensao_inferida
            dim_dir = no.dir.dimensao_inferida
            if no.op in ("+", "-") and dim_esq and dim_dir and dim_esq != dim_dir:
                self.erro(
                    no.linha,
                    no.coluna,
                    f"tipos incompativeis na operacao '{no.op}': nao e possivel combinar ingrediente de dimensao '{dim_esq}' com '{dim_dir}'",
                )
                no.tipo_inferido = "erro"
                return "erro"
            no.dimensao_inferida = dim_esq or dim_dir

            # Verificacao de divisao por zero literal
            if no.op == "/" and no.dir.classe == "Num" and no.dir.valor == 0:
                self.erro(
                    no.linha,
                    no.coluna,
                    "divisao por zero nao permitida na expressao",
                )
                no.tipo_inferido = "erro"
                return "erro"

            # Coercao sem perda: inteiro op real -> real (Aula 14 / Resumao G2)
            if t_esq == "real" or t_dir == "real" or no.op == "/":
                if t_esq != t_dir or (no.op == "/" and t_esq == "inteiro" and t_dir == "inteiro"):
                    no.campos["coercao"] = "inteiro -> real"
                no.tipo_inferido = "real"
                return "real"

            no.tipo_inferido = "inteiro"
            return "inteiro"

        no.tipo_inferido = "erro"
        return "erro"


# ============================================================================
# 5. PONTO DE ENTRADA (CLI)
# ============================================================================

def main():
    if len(sys.argv) < 2:
        print("uso: python src/semantico.py <arquivo> [--ast] [--tabela]", file=sys.stderr)
        return 2

    caminho = sys.argv[1]
    mostrar_ast = "--ast" in sys.argv
    mostrar_tabela = "--tabela" in sys.argv

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

    arvore_parse = parser.programa()

    erros_sintaticos = ouvinte_lexer.erros + ouvinte_parser.erros
    if erros_sintaticos:
        for linha, coluna, msg in sorted(erros_sintaticos):
            print(f"ERRO sintatico em {caminho}, linha {linha}, coluna {coluna}: {msg}", file=sys.stderr)
        return 1

    # 3. Construcao da AST via Visitor (Aula 14)
    construtor = ConstrutorAST()
    ast = construtor.visit(arvore_parse)

    # 4. Analise Semantica (Escopos, Tabela de Simbolos e Tipos)
    analisador = AnalisadorSemantico()
    erros_semanticos = analisador.analisar(ast)

    if erros_semanticos:
        for linha, coluna, msg in sorted(erros_semanticos):
            print(f"ERRO semantico em {caminho}, linha {linha}, coluna {coluna}: {msg}", file=sys.stderr)
        return 1

    print(f"OK semantico: '{caminho}' compilado e validado com sucesso.")

    if mostrar_ast:
        nos_parse = contar_nos_parse(arvore_parse)
        nos_ast = contar_nos_ast(ast)
        reducao = ((nos_parse - nos_ast) / nos_parse * 100) if nos_parse else 0.0
        print(f"\n--- Arvore Sintatica Abstrata (AST Anotada) ---")
        print(f"Reducao estrutural: Arvore de Parse = {nos_parse} nos -> AST = {nos_ast} nos (-{reducao:.1f}%)\n")
        imprimir_ast(ast)

    if mostrar_tabela:
        print("\n--- Tabela de Simbolos (Escopos) ---")
        imprimir_tabela_simbolos(analisador.tabelas)

    return 0


if __name__ == "__main__":
    sys.exit(main())
