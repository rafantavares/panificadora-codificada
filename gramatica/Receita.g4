lexer grammar Receita;

// ---- LEXER: MAIUSCULAS ----

// Passo: "passo" + numero (ex.: "passo 1", "passo2"). O parser agrupa
// tudo ate o proximo PASSO como o corpo daquele passo.
PASSO       : 'passo' [ \t]* [0-9]+ ;

// Palavras-chave (antes de IDENT: em empate, vence a primeira regra)
RECEITA     : 'receita' ;
PORCOES     : 'porcoes' ;
INGREDIENTE : 'ingrediente' ;
ACAO        : 'misture' | 'adicione' | 'bata' | 'amasse' | 'descanse'
            | 'asse' | 'cozinhe' | 'unte' | 'modele' | 'sirva' ;
PREPOSICAO  : 'em' | 'por' | 'a' | 'ate' | 'com' ;

// Unidades de medida
UNIDADE     : 'g' | 'kg' | 'ml' | 'l' | 'xicara' | 'colher' | 'pitada' | 'un' ;
TEMPO       : 'seg' | 'min' | 'h' ;
TEMPERATURA : 'graus' ;

// Literais
NUMERO      : [0-9]+ ('.' [0-9]+)? ;
TEXTO       : '"' ~["\r\n]* '"' ;
IDENT       : [a-zA-Z_][a-zA-Z_0-9]* ;

// Operadores e pontuacao
MAIS        : '+' ;
MENOS       : '-' ;
VEZES       : '*' ;
DIV         : '/' ;
IGUAL       : '=' ;
ABREPAR     : '(' ;
FECHAPAR    : ')' ;
VIRGULA     : ',' ;
DOISPONTOS  : ':' ;
PONTOVIRG   : ';' ;

// Descartados
COMENT      : '#' ~[\r\n]* -> skip ;
ESPACO      : [ \t\r\n]+ -> skip ;
