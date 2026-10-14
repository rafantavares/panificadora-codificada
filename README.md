# Panificadora Codificada

Linguagem de domínio específico (DSL) para descrever receitas culinárias estruturadas com ingredientes, unidades e passos de preparo.

Projeto desenvolvido para a disciplina de **Linguagens Formais e Computabilidade / Compiladores**.

---

## 📁 Estrutura do Repositório

O projeto está organizado em dois módulos principais:

1. **[`lexica/`](lexica/):** 
   - **Entrega 2 (E2):** Especificação da linguagem e Analisador Léxico.
   - Gramática léxica no ANTLR 4 (`Receita.g4`), analisador léxico (`src/lexico.py`), especificação completa (`docs/especificacao.md`), diário de decisões (`DIARIO.md`) e bateria de testes léxicos (`tests/test_exemplos.py`).

2. **[`sintatica/`](sintatica/):** 
   - **Entrega 3 (E3):** Analisador Sintático e Construção da Árvore Sintática (*Parse Tree*).
   - Gramática sintática livre de contexto (`gramatica/Receita.g4`), analisador sintático com árvore (`src/sintatico.py`), exemplos sintáticos válidos e inválidos, e suíte de testes automatizados (`tests/test_sintatico.py`).

---

## 🚀 Como Rodar os Projetos

Requer **Python 3** e **ANTLR 4.13.2** (`pip install -r requirements.txt`).

### Testando a Etapa Léxica (E2):
```sh
cd lexica
python tests/test_exemplos.py
python src/lexico.py exemplos/ola.rc
```

### Testando a Etapa Sintática (E3):
```sh
cd sintatica
python tests/test_sintatico.py
python src/sintatico.py exemplos/validos/ola.rc --tree
```
