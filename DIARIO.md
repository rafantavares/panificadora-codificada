# Diário

## 23/09
Definimos o domínio (leitor de receitas) e a ideia central: `passo N` abre
um passo que vai até o próximo `passo M`. No léxico, fizemos `PASSO` um único
token (`'passo' [ \t]* [0-9]+`), assim `passo 1` e `passo1` funcionam e o
parser só precisa agrupar o que vem depois.

Cuidado com ambiguidades: unidades (`g`, `l`, `h`, `a`) e palavras-chave
colidem com `IDENT`. No ANTLR, em empate vence a regra declarada primeiro,
então IDENT ficou depois das palavras-chave. Consequência: não dá para
chamar um ingrediente de `g` ou `a`.

Comentário: escolhemos `#` porque `/` é divisão (frações como `1/2 xicara`).

Números: `NUMERO` exige dígito depois do ponto, então `500.` vira `500` e um
`.` solto, que é reportado como número malformado.

Texto sem fechar: a regra `TEXTO` não casa sem a aspa final, então a `"`
sobra como caractere não reconhecido; o `lexico.py` traduz isso em
"texto sem fechar".

## 23/09 (tarde)
Rodamos `antlr4-parse Receita.g4 programa -tokens` e falhou: com
`lexer grammar` o antlr4-parse não aceita a gramática (precisa de uma regra
de parser). Trocamos para `grammar Receita;` com uma única regra provisória,
`programa : .*? EOF ;`, que aceita qualquer sequência de tokens e será
substituída na E3. Efeito colateral: o ANTLR passou a gerar `ReceitaLexer.py`
(antes era `Receita.py`), então o import em `lexico.py` mudou.

Também renomeamos os exemplos `quadrado.rc` e `espiral.rc` (herdados do
exemplo de desenho do enunciado) para `bolo_cenoura.rc` e `pao_forma.rc`,
que dizem o que realmente contêm.

## 23/09 (fim do dia)
Revisão de portabilidade: o Git no Windows converte fim de linha e um
`gerar.sh` com CRLF quebra no Linux/Mac. Adicionamos `.gitattributes`
forçando LF nos `.sh`. Fixamos as versões do ANTLR em `requirements.txt`.

Criamos dois inválidos novos: um com erro no meio de um passo e outro com
três erros no mesmo arquivo. O segundo confirmou que o analisador não para no
primeiro erro, ele segue e lista todos (texto sem fechar, `2.` e `?`).
