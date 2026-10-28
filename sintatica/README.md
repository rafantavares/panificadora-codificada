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

## Mensagens de Erro e Recuperação (Modo Pânico)

Toda mensagem de erro tem três partes: **onde** (linha e coluna), **o que esperava** e **o que encontrou**:

```
ERRO sintatico em exemplos/invalidos/falta_pontovirgula.rc, linha 4, coluna 1: esperava ';', encontrou 'passo 1'
```

Depois de um erro o analisador **não para**: ele entra em *modo pânico* (classe `ModoPanico` em [`src/sintatico.py`](src/sintatico.py)), descarta os tokens até um ponto seguro e recomeça dali. Assim todos os erros do arquivo aparecem de uma vez, mas sem *erros fantasmas* (mensagens que são só consequência do primeiro erro).

- **Pontos de sincronização:** `;` (fim de comando) e `passo N` (começo de bloco). Nunca um operador como `+`, que aparece no meio das expressões.
- Regras de dentro de um comando (`expr`, `argumento`, `modificador`...) param **antes** do `;`, para o próprio comando fechá-lo; os comandos e os laços de comandos consomem o `;` e seguem para o próximo.
- Exemplo do encontro 13 ([`erro_fantasma.rc`](exemplos/invalidos/erro_fantasma.rc)): `total = 1 + ) * ( + 2 * ) + 3;` gera **1** mensagem, não 5.
- [`varios_erros.rc`](exemplos/invalidos/varios_erros.rc) tem 3 erros reais em comandos diferentes e gera exatamente 3 mensagens.

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

Roda os 3 programas válidos e os 8 programas inválidos (com erros sintáticos propositais como falta de ponto e vírgula, parênteses desbalanceados, comandos fora de passo, erro fantasma e vários erros no mesmo arquivo). Para cada inválido o teste confere o trecho da mensagem e **quantas** mensagens saíram (um erro real = uma mensagem).
