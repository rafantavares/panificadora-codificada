grammar Receita;

// ==========================================
// PARSER (E3): REGRAS SINTÁTICAS (minúsculas)
// ==========================================

programa
    : declaracao_receita? declaracao_porcoes? declaracao_global* bloco_passo* EOF
    ;

declaracao_receita
    : RECEITA TEXTO PONTOVIRG
    ;

declaracao_porcoes
    : PORCOES NUMERO PONTOVIRG
    ;

declaracao_global
    : declaracao_ingrediente
    | atribuicao
    ;

declaracao_ingrediente
    : INGREDIENTE IDENT expr UNIDADE PONTOVIRG
    ;

atribuicao
    : IDENT IGUAL expr PONTOVIRG
    ;

bloco_passo
    : PASSO DOISPONTOS comando_passo*
    ;

comando_passo
    : comando_acao
    | atribuicao
    ;

comando_acao
    : ACAO lista_argumentos? modificador* PONTOVIRG
    ;

lista_argumentos
    : argumento (VIRGULA argumento)*
    ;

argumento
    : IDENT
    | TEXTO
    ;

modificador
    : PREPOSICAO complemento
    ;

complemento
    : expr (TEMPO | TEMPERATURA)?
    | IDENT
    | TEXTO
    ;

// Precedência de operadores: a declarada primeiro liga mais forte!
expr
    : ABREPAR expr FECHAPAR
    | expr (VEZES | DIV) expr
    | expr (MAIS | MENOS) expr
    | NUMERO
    | IDENT
    ;


// ==========================================
// LEXER (E2): REGRAS LÉXICAS (MAIÚSCULAS)
// ==========================================

PASSO       : 'passo' [ \t]* [0-9]+ ;

RECEITA     : 'receita' ;
PORCOES     : 'porcoes' ;
INGREDIENTE : 'ingrediente' ;
ACAO        : 'misture' | 'adicione' | 'bata' | 'amasse' | 'descanse'
            | 'asse' | 'cozinhe' | 'unte' | 'modele' | 'sirva' ;
PREPOSICAO  : 'em' | 'por' | 'a' | 'ate' | 'com' ;

UNIDADE     : 'g' | 'kg' | 'ml' | 'l' | 'xicara' | 'colher' | 'pitada' | 'un' ;
TEMPO       : 'seg' | 'min' | 'h' ;
TEMPERATURA : 'graus' ;

NUMERO      : [0-9]+ ('.' [0-9]+)? ;
TEXTO       : '"' ~["\r\n]* '"' ;
IDENT       : [a-zA-Z_][a-zA-Z_0-9]* ;

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

COMENT      : '#' ~[\r\n]* -> skip ;
ESPACO      : [ \t\r\n]+ -> skip ;
