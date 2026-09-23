"""Roda o lexico em todos os exemplos: validos devem passar, invalidos devem falhar."""
import glob
import os
import subprocess
import sys

RAIZ = os.path.join(os.path.dirname(__file__), "..")
LEXICO = os.path.join(RAIZ, "src", "lexico.py")
falhas = 0


def rodar(arq):
    return subprocess.run([sys.executable, LEXICO, arq], capture_output=True, text=True)


for arq in sorted(glob.glob(os.path.join(RAIZ, "exemplos", "*.rc"))):
    ok = rodar(arq).returncode == 0
    print(("OK   " if ok else "FALHA"), "valido  ", os.path.basename(arq))
    falhas += not ok

esperado = {"caractere_invalido": "caractere invalido", "texto_sem_fechar": "texto sem fechar",
            "numero_malformado": "numero malformado"}
for arq in sorted(glob.glob(os.path.join(RAIZ, "exemplos", "invalidos", "*.rc"))):
    r = rodar(arq)
    nome = os.path.basename(arq)[:-3]
    ok = r.returncode == 1 and esperado[nome] in r.stderr and "linha" in r.stderr
    print(("OK   " if ok else "FALHA"), "invalido", os.path.basename(arq))
    falhas += not ok

sys.exit(1 if falhas else 0)
