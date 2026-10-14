# Especificação · Panificadora Codificada

## 1. Para que serve

A linguagem descreve receitas culinárias de forma estruturada: ingredientes com quantidade e unidade, e uma sequência de passos numerados. O objetivo é permitir que um programa leia a receita, separe os passos e valide medidas, tempos e temperaturas.

## 2. Programa de exemplo

```
# Receita minima                              (1) comentário, descartado
receita "Pao simples";                        (2) nome da receita
porcoes 4;                                    (3) rendimento

ingrediente farinha 500 g;                    (4) nome, quantidade, unidade
ingrediente agua 300 ml;                      (5) idem

passo 1:                                      (6) abre o passo 1 (vale até o próximo "passo N")
  misture farinha, agua;                      (7) ação sobre ingredientes separados por vírgula
passo 2:                                      (8) fecha o passo 1 e abre o passo 2
  asse por 40 min a 180 graus;                (9) ação + tempo + temperatura
```

## 3. Tipos de dado

| tipo | exemplos | token |
|---|---|---|
| número (inteiro ou real) | `500`, `2.5` | `NUMERO` |
| texto | `"Pao simples"` | `TEXTO` |
| nome (ingrediente/variável) | `farinha`, `agua_morna` | `IDENT` |
| quantidade | `500 g`, `1 colher` | `NUMERO` + `UNIDADE` |
| tempo | `40 min`, `1 h` | `NUMERO` + `TEMPO` |
| temperatura | `180 graus` | `NUMERO` + `TEMPERATURA` |

Unidades: `g kg ml l xicara colher pitada un`. Tempos: `seg min h`.

## 4. Comandos

- `receita "nome";` — nomeia a receita.
- `porcoes N;` — rendimento.
- `ingrediente NOME QTD UNIDADE;` — declara um ingrediente.
- `passo N:` — inicia o passo N. Tudo até o próximo `passo M` pertence a ele (`passo 1` e `passo1` são equivalentes).
- Ações dentro de um passo: `misture`, `adicione`, `bata`, `amasse`, `descanse`, `asse`, `cozinhe`, `unte`, `modele`, `sirva`. Podem levar ingredientes (separados por `,`), textos e as preposições `em por a ate com` seguidas de tempo/temperatura.
- `NOME = expressão;` — atribuição de valor numérico (ex.: `total = 1000 + 600 * 2;`).

Toda instrução termina com `;`, exceto a linha `passo N:`.

## 5. Operadores e precedência

Do maior para o menor: 

1. `( )` — agrupamento
2. `*` `/` — multiplicação e divisão (esquerda para direita)
3. `+` `-` — soma e subtração (esquerda para direita)
4. `=` — atribuição

Pontuação: `,` separa itens, `;` termina instrução, `:` segue `passo N`.

## 6. Comentários

Começam com `#` e vão até o fim da linha. São descartados pelo analisador. (`//` foi descartado porque `/` já é divisão.)

## 7. O que a linguagem deliberadamente não faz

1. **Não tem laços nem condicionais.** Uma receita é uma sequência linear; "repita até dourar" é texto humano, não lógica executável.
2. **Não converte unidades automaticamente** (g ↔ xícara). Cada ingrediente mantém a unidade em que foi declarado, pois a conversão depende do ingrediente.
3. **Não tem tipos definidos pelo usuário nem funções.** Só existem os tipos da seção 3; receitas não chamam outras receitas.
