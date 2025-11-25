from ply import lex, yacc
from sys import argv, exit
class HackCodeAnalyze:
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
        # self.yacc = yacc.yacc(module=self, **kwargs)
    
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
        self.varTable          = {
            'SP': 0, 
            'LCL': 1, 
            'ARG': 2, 
            'THIS': 3, 
            'THAT': 4,
            'SCREEN': 16384, 
            'KBD': 24576
        }
        
        for i in range(16):
            self.varTable[f'R{i}'] = i

        self.t_ignore           = ' \t'     # A string containing ignored characters (spaces and tabs)
        self.t_ignore_comment   = r'//.*'

        self.tokens         = (         # tokensの要素に t_を付けると定義可能
            'AT',       # '@'
            'LPAREN',   # '('
            'RPAREN',   # ')'
            'EQUAL',    # '='
            'SEMI',     # ';'
            'PLUS',     # '+'
            'MINUS',    # '-'
            'AND',      # '&'
            'OR',       # '|'
            'NOT',      # '!'
            'NUMBER',
            'SYMBOL',
        )
        
        self.t_AT       = r'@'
        self.t_LPAREN   = r'\('
        self.t_RPAREN   = r'\)'
        self.t_EQUAL    = r'='
        self.t_SEMI     = r';'
        self.t_PLUS     = r'\+'
        self.t_MINUS    = r'-'
        self.t_AND      = r'&'
        self.t_OR       = r'\|'
        self.t_NOT      = r'!'

    
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
        r'[A-Za-z_\.\$:][A-Za-z0-9_\.\$:]*'
        return t
    
    def p_error(self, p):
        print("Syntax error at", p)

    def p_statements_1(self, p):
        "statements : statement statements"

    def p_statements_2(self, p):
        "statements : empty"
        p[0] = p[1]

    def p_empty_1(self, p):
        "empty : "

    def p_statement_1(self, p):
        "statement : p_instruction"
        p[0] = p[1]

    def p_statement_2(self, p):
        "statement : a_instruction"
        p[0] = p[1]

    def p_statement_3(self, p):
        "statement : l_instruction"
        p[0] = p[1]

    # ここに構文解析の規則を追加

    

if __name__ == "__main__":
    if len(argv) < 2:
        file = "main.asm"
    else:
        file = argv[1]

    with open(file, "r", encoding="UTF-8") as source:
        program = source.read()

    with HackCodeAnalyze(program) as l:
        print(l)
        # result = l.parse()

    input("終了")