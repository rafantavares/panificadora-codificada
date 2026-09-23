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
