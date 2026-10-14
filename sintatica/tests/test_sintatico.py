"""Bateria de testes do analisador sintatico (E3).

Valida que todos os programas validos passam sem erro e todos os invalidos falham
apontando o erro sintatico com linha e coluna.
"""
import glob
import os
import subprocess
import sys

RAIZ = os.path.join(os.path.dirname(__file__), "..")
SINTATICO = os.path.join(RAIZ, "src", "sintatico.py")
falhas = 0


def rodar(arq):
    return subprocess.run([sys.executable, SINTATICO, arq], capture_output=True, text=True)


print("=== TESTES DE SINTAXE VALIDA ===")
for arq in sorted(glob.glob(os.path.join(RAIZ, "exemplos", "validos", "*.rc"))):
    r = rodar(arq)
    ok = (r.returncode == 0) and ("OK sintatico" in r.stdout)
    print(("OK   " if ok else "FALHA"), "valido  ", os.path.basename(arq))
    falhas += not ok

print("\n=== TESTES DE SINTAXE INVALIDA ===")
esperados = {
    "falta_pontovirgula": "faltou ';'",
    "passo_sem_doispontos": "faltou ':'",
    "parenteses_desbalanceados": "faltou ')'",
    "expressao_malformada": "ERRO sintatico",
    "comando_fora_do_passo": "ERRO sintatico",
    "ingrediente_sem_unidade": "ERRO sintatico",
}

for arq in sorted(glob.glob(os.path.join(RAIZ, "exemplos", "invalidos", "*.rc"))):
    r = rodar(arq)
    nome = os.path.basename(arq)[:-3]
    trecho = esperados.get(nome, "ERRO sintatico")
    ok = (r.returncode == 1) and (trecho in r.stderr) and ("linha" in r.stderr)
    print(("OK   " if ok else "FALHA"), "invalido", os.path.basename(arq))
    falhas += not ok

print()
if falhas == 0:
    print("Todos os testes passaram com sucesso!")
    sys.exit(0)
else:
    print(f"{falhas} teste(s) falharam.")
    sys.exit(1)
