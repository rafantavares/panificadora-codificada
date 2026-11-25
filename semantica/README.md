# Panificadora Codificada — Construção da AST e Analisador Semântico (E4 / E5)

Nesta etapa final (Encontros 13 a 16), o compilador da **Panificadora Codificada** transforma a Árvore de Parse gerada pelo ANTLR em uma **Árvore Sintática Abstrata (AST)** enxuta e realiza a **análise semântica** completa com **Pilha de Tabelas de Símbolos (escopos)** e **Verificação e Inferência de Tipos com Coerção**.

---

## 1. Da Árvore de Parse para a AST (`ConstrutorAST`)

A árvore de parse do ANTLR carrega todos os detalhes da gramática: regras intermediárias de precedência/andaime (`declaracao_global`, `comando_passo`, `lista_argumentos`, `argumento`, `complemento`) e tokens de pontuação (`;`, `:`, `=`, `(`, `)`, `,`).

A classe `ConstrutorAST(ReceitaVisitor)` em [`src/semantico.py`](src/semantico.py) percorre a árvore de parse e constrói a AST com objetos da classe `No(classe, linha, coluna, **campos)`:

- **Regra de 1 filho (repasse):** `if ctx.getChildCount() == 1: return self.visit(ctx.getChild(0))` elimina nós intermediários de repasse.
- **Agrupamento com parênteses:** `( expr )` define a topologia da árvore na etapa sintática e retorna diretamente a subárvore interna sem criar nó `Paren`.
- **Redução estrutural (~69%):**
  - `ola.rc`: **58 nós** na Árvore de Parse $\rightarrow$ **18 nós** na AST (**-69,0%**).
  - `bolo_cenoura.rc`: **107 nós** na Árvore de Parse $\rightarrow$ **33 nós** na AST (**-69,2%**).
  - `pao_forma.rc`: **153 nós** na Árvore de Parse $\rightarrow$ **47 nós** na AST (**-69,3%**).

### Nós da AST
| Classe do Nó | Campos Principais | Papel Semântico |
| :--- | :--- | :--- |
| `Programa` | `receita`, `porcoes`, `declaracoes`, `passos` | Raiz do programa `.rc` |
| `Receita` | `nome` | Título da receita (`texto`) |
| `Porcoes` | `qtd` | Rendimento da receita (`inteiro > 0`) |
| `Declara` | `nome`, `qtd`, `unidade` | Declaração de ingrediente com quantidade e unidade física |
| `Atribui` | `alvo`, `valor` | Atribuição/declaração de variável calculada |
| `Passo` | `numero`, `comandos` | Bloco de passo de preparo (abre novo escopo local) |
| `Acao` | `verbo`, `argumentos`, `modificadores` | Ação culinária (`misture`, `bata`, `asse`, `unte`, etc.) |
| `Modificador` | `preposicao`, `valor`, `medida` | Condição de tempo (`min`, `h`), temperatura (`graus`) ou recipiente (`em forma`) |
| `Op` | `op`, `esq`, `dir` | Operação aritmética binária (`+`, `-`, `*`, `/`) |
| `Num`, `Texto`, `Var` | `valor` / `nome` | Folhas da AST com linha, coluna e `tipo_inferido` |

---

## 2. Pilha de Tabelas de Símbolos e Escopos (`PilhaTabelas`)

Implementada como uma **pilha de dicionários** (`self.pilha = [{}]`), seguindo a arquitetura da Aula 14 (slide 21):

- **Escopo Global (`pilha[0]`):** Armazena ingredientes (`ingrediente farinha 500 g;`) e variáveis globais (`total = 1000 + 600 * 2;`).
- **Escopo Local por Passo (`passo N:`):** Ao entrar em `visitar_passo`, o analisador chama `empilhar("passo N")`; ao terminar o passo, chama `desempilhar()`. Variáveis locais criadas dentro de um passo deixam de existir ao final dele.
- **`declarar(nome, simbolo)`:** Olha **apenas o escopo do topo** (`self.pilha[-1]`). Se o nome já existe no mesmo escopo, reporta erro de declaração duplicada; se existe apenas em escopo externo, permite o **sombreamento** (*shadowing*).
- **`buscar(nome)`:** Percorre a pilha **do topo para a base** (`for escopo in reversed(self.pilha)`), encontrando a definição mais próxima.

---

## 3. Verificação Semântica, Inferência de Tipos e Coerção

A verificação de tipos funciona com **atributos sintetizados** (calculados de baixo para cima nas expressões da AST), anotando `no.tipo_inferido` e `no.dimensao_inferida` em cada nó:

1. **Ingrediente ou variável não declarada:**
   - Em expressões (`total = farinha + taxa;`) $\rightarrow$ `variavel ou ingrediente 'taxa' usado em expressao sem ter sido declarado`.
   - Em ações culinárias (`misture farinha, chocolate;`) $\rightarrow$ `ingrediente 'chocolate' usado em 'misture' sem ter sido declarado`.
2. **Declaração duplicada no mesmo escopo:**
   - Declarar `ingrediente farinha` duas vezes $\rightarrow$ `ingrediente 'farinha' declarado duas vezes no mesmo escopo (ja declarado na linha 5)`.
3. **Visibilidade de escopo local:**
   - Usar no `passo 2` uma variável `tempo_local` declarada apenas no `passo 1` $\rightarrow$ erro de variável não declarada após o `desempilhar()`.
4. **Inferência de tipos (`inteiro`, `real`, `texto`) e Coerção sem perda:**
   - `inteiro` op `inteiro` (`+`, `-`, `*`) $\rightarrow$ `inteiro`.
   - `inteiro` op `real` ou divisão `/` $\rightarrow$ `real`, anotando `(coercao: inteiro -> real)` no nó da AST.
   - Atribuir `real` a uma variável já declarada como `inteiro` (`lotes = 2; lotes = 2.5;`) é rejeitado por perda de precisão.
5. **Compatibilidade dimensional de unidades físicas e divisão por zero:**
   - Somar ou subtrair ingredientes de dimensões físicas diferentes (`massa` em `g/kg` + `volume` em `ml/l`, ex.: `mistura = farinha + agua;`) gera erro semântico dimensional.
   - Divisão por literal zero (`500 / 0`) é detectada e rejeitada.

---

## 4. Como Executar

### Analisar uma Receita, Exibir a AST Anotada e a Tabela de Símbolos
```sh
# Validação semântica
python src/semantico.py exemplos/validos/pao_forma.rc

# Exibir AST anotada (com tipos inferidos, coerções e % de redução de nós) e Tabela de Símbolos
python src/semantico.py exemplos/validos/bolo_cenoura.rc --ast --tabela
```

### Rodar a Bateria Automatizada de Testes Semânticos
```sh
python tests/test_semantico.py
```
Valida os **4 programas válidos** (`bolo_cenoura.rc`, `escopos_e_coercao.rc`, `ola.rc`, `pao_forma.rc`) e os **8 casos de erro semântico** em `exemplos/invalidos/`.
