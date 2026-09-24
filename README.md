# Panificadora Codificada

Linguagem para escrever receitas: ingredientes com medidas e uma sequência de passos (`passo 1`, `passo 2`...), tudo entre um `passo N` e o próximo pertence àquele passo.

```
receita "Pao simples";
porcoes 4;
ingrediente farinha 500 g;
ingrediente agua 300 ml;
passo 1:
  misture farinha, agua;
passo 2:
  asse por 40 min a 180 graus;
```

Especificação completa: [docs/especificacao.md](docs/especificacao.md) · Diário: [DIARIO.md](DIARIO.md)

## Instalar e rodar

Requer Python 3. Versões usadas: **ANTLR 4.13.2** (antlr4-tools 0.2.2, runtime `antlr4-python3-runtime` 4.13.2), Java 17.

```sh
pip install -r requirements.txt
sh gerar.sh                                  # gera gerado/ (não versionado)
python src/lexico.py exemplos/ola.rc         # lista os tokens
```

Erros léxicos são reportados com linha e coluna (saída de erro, código de saída 1).

## Fase atual

**E2 — especificação e analisador léxico.** Parser (E3) e semântica (E4) ainda não iniciados.

## Testes

```sh
python tests/test_exemplos.py
```

Roda o léxico nos exemplos válidos (devem passar) e em `exemplos/invalidos/` (devem falhar apontando o erro).

## Testando só a gramática (sem gerar código)

```sh
cd gramatica && antlr4-parse Receita.g4 programa -tokens ../exemplos/ola.rc
```
