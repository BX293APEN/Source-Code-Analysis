from ply import lex, yacc

class LexicalAnalyze:
    """オブジェクトの説明
| method | args | description |
| - | - | - |
| .__init__ | code | codeの中に解析するコードの文字列を入れる |
| .set_code | code | codeの中に解析するコードの文字列を入れる |
| .build | **kwargs | lexにオブジェクトを認識させる(ブロック構文で自動実行) |
| .get_tokens | - | lexで字句解析をし、トークン化する |
| .parse | - | YACCで構文解析をし、トークン化する |
    """

    def set_code(self,code = ""):
        self.code = code

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        self.yacc = yacc.yacc(module=self, **kwargs)
    
    def parse(self): # yacc による構文解析
        return self.yacc.parse(self.code, lexer=self.lexer)
    
    def get_tokens(self):
        self.lexer.input(self.code)
        self.sourceTokenList  = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            self.sourceTokenList.append(tok)
        return self.sourceTokenList

    def __str__(self):
        self.get_tokens()
        return "\n".join([str(t) for t in self.sourceTokenList])

    def __enter__(self):
        self.build()
        return self
    
    def __exit__(self, *args):
        pass

    def __init__(self, code = ""):
        self.set_code(code)
        self.symbolTable = {}

        self.t_ignore       = ' \t'     # A string containing ignored characters (spaces and tabs)
        
        self.tokens         = (         # tokensの要素に t_を付けると定義可能
            'NUMBER',
            'EQUAL',
            'PLUS',
            'MINUS',
            'TIMES',
            'DIVIDE',
            'LPAREN',
            'RPAREN',
            'SYMBOL',
            'PRINT',
        )
        
        self.t_EQUAL        = r'='
        self.t_PLUS         = r'\+'
        self.t_MINUS        = r'-'
        self.t_TIMES        = r'\*'
        self.t_DIVIDE       = r'/'
        self.t_LPAREN       = r'\('
        self.t_RPAREN       = r'\)'

    
    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # A regular expression rule with some action code
    # Note addition of self parameter since we're in a class
    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t
    
    def t_SYMBOL(self, t):
        r'[A-Z]+'
        if t.value == "PRINT":
            t.type = "PRINT"
        return t

    def p_statements_1(self, p):
        "statements : statement statements"

    def p_statements_2(self, p):
        "statements : empty"
        p[0] = p[1]

    def p_empty_1(self, p):
        "empty : "

    def p_statement_1(self, p):
        "statement : p_statement"
        p[0] = p[1]

    def p_statement_2(self, p):
        "statement : a_statement"
        p[0] = p[1]

    def p_pstatement_1(self, p):
        "p_statement : PRINT expression"
        print(p[2])

    def p_astatement_1(self, p):
        "a_statement : SYMBOL EQUAL expression"
        name = p[1]
        value = p[3]
        self.symbolTable[name] = value
        p[0] = value

    def p_expression_1(self, p):
        "expression : expression PLUS term"
        p[0] = p[1] + p[3]

    def p_expression_2(self, p):
        "expression : expression MINUS term"
        p[0] = p[1] - p[3]

    def p_expression_3(self, p):
        "expression : term"
        p[0] = p[1]

    def p_term_1(self, p):
        "term : term TIMES factor"
        p[0] = p[1] * p[3]

    def p_term_2(self, p):
        "term : term DIVIDE factor"
        p[0] = p[1] // p[3]

    def p_term_3(self, p):
        "term : factor"
        p[0] = p[1]


    def p_factor_1(self, p):
        "factor : num"
        p[0] = p[1]

    def p_factor_2(self, p):
        "factor : MINUS num"
        p[0] = - p[2]
    
    def p_factor_3(self, p):
        "factor : LPAREN expression RPAREN"
        p[0] = (p[2])

    def p_num_1(self, p):
        "num : NUMBER"
        p[0] = p[1]

    def p_num_2(self, p):
        "num : SYMBOL"
        name = p[1]
        if name in self.symbolTable:
            p[0] = self.symbolTable[name]
        else:
            print(f"undefined : {name}")
            p[0] = 0
    

    def p_error(self, p):
        print("Syntax error at", p)

if __name__ == "__main__":
    with open("main.txt", "r", encoding="UTF-8") as source:
        program = source.read()

    with LexicalAnalyze(program) as l:
        result = l.parse()

    input("終了")