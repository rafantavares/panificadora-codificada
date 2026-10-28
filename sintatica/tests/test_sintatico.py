"""Bateria de testes do analisador sintatico (E3).

Valida que todos os programas validos passam sem erro e todos os invalidos falham
apontando onde (linha e coluna), o que esperava e o que encontrou, com uma
mensagem por erro real (modo panico, sem erros fantasmas).
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
# Para cada invalido: trecho que a mensagem precisa ter e quantas mensagens
# devem sair (um erro real = uma mensagem, sem fantasmas)
esperados = {
    "comando_fora_do_passo": ("encontrou 'misture'", 1),
    "erro_fantasma": ("encontrou ')'", 1),
    "expressao_malformada": ("encontrou '*'", 1),
    "falta_pontovirgula": ("esperava ';', encontrou 'passo 1'", 1),
    "ingrediente_sem_unidade": ("esperava uma unidade", 1),
    "parenteses_desbalanceados": ("ou ')', encontrou 'min'", 1),
    "passo_sem_doispontos": ("esperava ':', encontrou 'misture'", 1),
    "varios_erros": ("esperava uma unidade", 3),
}

for arq in sorted(glob.glob(os.path.join(RAIZ, "exemplos", "invalidos", "*.rc"))):
    r = rodar(arq)
    nome = os.path.basename(arq)[:-3]
    trecho, qtd = esperados.get(nome, ("ERRO sintatico", 1))
    mensagens = r.stderr.strip().splitlines()
    ok = (r.returncode == 1) and (trecho in r.stderr) and ("linha" in r.stderr) \
        and len(mensagens) == qtd
    print(("OK   " if ok else "FALHA"), "invalido", os.path.basename(arq), f"({len(mensagens)} msg)")
    falhas += not ok

print()
if falhas == 0:
    print("Todos os testes passaram com sucesso!")
    sys.exit(0)
else:
    print(f"{falhas} teste(s) falharam.")
    sys.exit(1)
