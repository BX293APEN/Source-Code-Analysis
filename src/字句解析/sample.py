from ply import lex

class LexicalAnalyze:
    """オブジェクトの説明
| method | args | description |
| - | - | - |
| .__init__ | code | codeの中に解析するコードの文字列を入れる |
| .set_code | code | codeの中に解析するコードの文字列を入れる |
| .build | **kwargs | lexにオブジェクトを認識させる(ブロック構文で自動実行) |
| .get_tokens | - | lexで字句解析をし、トークン化する |
    """

    def set_code(self,code = ""):
        self.code = code

    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
    
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


if __name__ == "__main__":
    with open("main.txt", "r", encoding="UTF-8") as source:
        program = source.read()

    with LexicalAnalyze(program) as l:
        print(l)
    input()