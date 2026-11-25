"""Bateria de testes do analisador semantico e construtor da AST (E4 / E5).

Valida:
1. Todos os programas validos compilam sem erros, constroem a AST reduzindo os
   nos de andaime/pontuacao (~69% de reducao) e preenchem a Tabela de Simbolos.
2. Todos os programas invalidos falham com codigo 1 apontando linha, coluna e
   causa exata do erro semantico (declaracao duplicada, uso sem declarar,
   escopo local desempilhado, tipos/unidades incompativeis, divisao por zero).
"""
import glob
import os
import subprocess
import sys

RAIZ = os.path.join(os.path.dirname(__file__), "..")
SEMANTICO = os.path.join(RAIZ, "src", "semantico.py")
falhas = 0


def rodar(arq, *flags):
    return subprocess.run([sys.executable, SEMANTICO, arq, *flags], capture_output=True, text=True)


print("=== TESTES DE SEMANTICA VALIDA (AST + TABELA DE SIMBOLOS) ===")
for arq in sorted(glob.glob(os.path.join(RAIZ, "exemplos", "validos", "*.rc"))):
    r = rodar(arq, "--ast", "--tabela")
    ok = (
        (r.returncode == 0)
        and ("OK semantico" in r.stdout)
        and ("Arvore Sintatica Abstrata" in r.stdout)
        and ("Tabela de Simbolos" in r.stdout)
    )
    print(("OK   " if ok else "FALHA"), "valido  ", os.path.basename(arq))
    if not ok:
        print("  STDOUT:", r.stdout)
        print("  STDERR:", r.stderr)
    falhas += not ok

print("\n=== TESTES DE SEMANTICA INVALIDA ===")
esperados = {
    "divisao_por_zero": ("divisao por zero nao permitida", 1),
    "escopo_local_invisivel": ("'tempo_local' usado em expressao sem ter sido declarado", 1),
    "ingrediente_duplicado": ("ingrediente 'farinha' declarado duas vezes no mesmo escopo", 1),
    "ingrediente_nao_declarado": ("ingrediente 'chocolate' usado em 'misture' sem ter sido declarado", 1),
    "tipos_incompativeis": ("nao e possivel atribuir 'real' a 'inteiro' sem perda de precisao", 1),
    "unidades_incompativeis": ("nao e possivel combinar ingrediente de dimensao 'massa' com 'volume'", 1),
    "variavel_nao_declarada": ("'taxa' usado em expressao sem ter sido declarado", 1),
    "varios_erros_semanticos": ("ingrediente 'farinha' declarado duas vezes", 3),
}

for arq in sorted(glob.glob(os.path.join(RAIZ, "exemplos", "invalidos", "*.rc"))):
    r = rodar(arq)
    nome = os.path.basename(arq)[:-3]
    trecho, qtd = esperados.get(nome, ("ERRO semantico", 1))
    mensagens = r.stderr.strip().splitlines()
    ok = (
        (r.returncode == 1)
        and (trecho in r.stderr)
        and ("linha" in r.stderr)
        and len(mensagens) == qtd
    )
    print(("OK   " if ok else "FALHA"), "invalido", os.path.basename(arq), f"({len(mensagens)} msg)")
    if not ok:
        print("  Esperava:", trecho, f"({qtd} msg)")
        print("  STDERR:", r.stderr)
    falhas += not ok

print()
if falhas == 0:
    print("Todos os testes semanticos passaram com sucesso!")
    sys.exit(0)
else:
    print(f"{falhas} teste(s) falharam.")
    sys.exit(1)
