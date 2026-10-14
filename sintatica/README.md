# Panificadora Codificada — Analisador Sintático (E3)

Nesta etapa (E3), a linguagem ganha a **análise sintática** e a construção da **árvore sintática** (*parse tree*), garantindo que as frases e comandos da receita sigam a gramática formal da linguagem.

## Regras Sintáticas Principais

A gramática [`gramatica/Receita.g4`](gramatica/Receita.g4) define:

1. **Estrutura Geral:** Uma receita pode ter cabeçalho (`receita "Nome";`, `porcoes N;`), declarações de ingredientes/variáveis globais e uma sequência de passos (`passo 1: ...`).
2. **Declaração de Ingredientes:** `ingrediente farinha 500 g;` ou com frações `ingrediente acucar 1/2 xicara;`.
3. **Passos:** Iniciados por `passo N:` contendo comandos de ação (`misture`, `bata`, `asse`, etc.) ou atribuições.
4. **Precedência de Expressões Aritméticas:**
   - Agrupamento com parênteses `( )`
   - Multiplicação e divisão (`*`, `/`)
   - Adição e subtração (`+`, `-`)
   - Termos numéricos e identificadores

## Como Executar

### 1. Recompilar o Parser (ANTLR)
```sh
sh gerar.sh
# ou no Windows:
gerar.bat
```

### 2. Analisar um Arquivo e Ver a Árvore Sintática
```sh
# Apenas validação sintática
python src/sintatico.py exemplos/validos/ola.rc

# Exibindo a árvore sintática gerada (S-Expression e indentada)
python src/sintatico.py exemplos/validos/ola.rc --tree
```

### 3. Rodar a Bateria de Testes Sintáticos
```sh
python tests/test_sintatico.py
```

Roda os 3 programas válidos e os 6 programas inválidos (com erros sintáticos propositais como falta de ponto e vírgula, parênteses desbalanceados, comandos fora de passo, etc.).
