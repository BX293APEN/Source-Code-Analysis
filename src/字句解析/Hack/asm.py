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

    def __init__(
        self, 
        code = "", 
        ram = 65536,
        debug = True
    ):
        self.debug              = debug
        self.set_code(code)

        self.varTable           = {
            'SP': 0, 
            'LCL': 1, 
            'ARG': 2, 
            'THIS': 3, 
            'THAT': 4,
            'SCREEN': 16384, 
            'KBD': 24576
        }
        
        self.registerNum = 16
        for i in range(self.registerNum):
            self.varTable[f'R{i}'] = i

        self.nextVarAddr = self.registerNum

        self.registers = {"A": 0, "D": 0} # レジスタ値
        self.ram = [0] * ram
        self.pc = 0

        self.t_ignore           = ' \t'     # A string containing ignored characters (spaces and tabs)
        self.t_ignore_comment   = r'//.*'

        self.reservedWords = (
            'AMD',
            'AD', 
            'AM', 
            'MD', 
            'A', 
            'M', 
            'D', 
            'JGT', 
            'JEQ', 
            'JGE', 
            'JLT', 
            'JNE', 
            'JLE', 
            'JMP'
        )

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

        ) + self.reservedWords
        
        
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
        if t.value in self.reservedWords:
            t.type = t.value
        return t
    


    # 構文解析
    def p_error(self, p):
        print("Syntax error at", p)

    def p_statements(self, p):
        """
        statements  : statement statements
                    | empty
        """
        if len(p) == 3:
            p[0] = [p[1]] + p[2]
        else:
            p[0] = []

    def p_empty(self, p):
        "empty : "

    def p_statement_a(self, p):
        "statement  : a_instruction"
        p[0] = p[1]
        if self.debug:
            print("A命令")
        
        self.pc += 1
    
    def p_statement_l(self, p):
        "statement  : l_instruction"
        p[0] = p[1]
        if self.debug:
            print("Label")
    
    def p_statement_c(self, p):
        "statement  : c_instruction"
        p[0] = p[1]
        if self.debug:
            print("C命令")
        
        self.pc += 1

    
    def get_next_addr(self):
        value = None
        if self.nextVarAddr < self.varTable['SCREEN']:
            value = self.nextVarAddr
        self.nextVarAddr += 1
        return value

    # A命令
    def p_a_instruction(self, p):
        """
        a_instruction   : AT SYMBOL
                        | AT NUMBER
        """
        if isinstance(p[2], int):
            value = p[2]
            if self.debug:
                print(f"0{value:015b}")
        else:
            label = str(p[2])
            if label not in self.varTable:
                addr = self.get_next_addr()
                if addr is not None:
                    self.varTable[label] = addr
            value = self.varTable[label]

        self.registers["A"] = value

        p[0] = {"type": "A", "value": value}
        

    
    # L命令 (LABEL)
    def p_l_instruction(self, p):
        """
        l_instruction : LPAREN SYMBOL RPAREN
        """
        label = p[2]
        self.varTable[label] = self.pc

        p[0] = {"type": "L", "label": label}

    #   C 命令
    # dest=comp;jump
    def p_c_instruction_1(self, p):
        """
        c_instruction   : dest EQUAL comp SEMI jump
                        | comp SEMI jump
                        | dest EQUAL comp
                        | comp
        
        """

        dest = None
        comp = None
        jump = None

        if len(p) == 2:
            comp = p[1]
        elif len(p) == 4 and p.slice[2].type == "SEMI":
            comp = p[1]
            jump = p[3]
        elif len(p) == 4 and p.slice[2].type == "EQUAL":
            dest = p[1]
            comp = p[3]
        elif len(p) == 6:
            dest = p[1]
            comp = p[3]
            jump = p[5]

        value = self.eval_comp(comp)

        # 000
        if dest:
            if "A" in dest: # 100
                self.registers["A"] = value
            if "D" in dest: # 010
                self.registers["D"] = value
            if "M" in dest: # 001
                addr            = self.registers["A"]
                self.ram[addr]  = value

        p[0] = {
            "type": "C",
            "dest": dest,
            "comp": comp,
            "jump": jump,
            "value": value,
        }


    def p_dest(self, p):
        """
        dest    : AMD
                | AD
                | AM
                | MD 
                | A
                | M
                | D
        """
        p[0] = str(p[1])

    def p_comp(self, p):
        """
        comp        : registers
                    | registerNum
                    | registerFunc
                    | register
                    | num
        """
        p[0] = p[1]
    
    def p_registers(self, p):
        """
        registers       : register PLUS register
                        | register MINUS register
                        | register AND register
                        | register OR register
        """

        p[0] = {"op": p[2], "left": p[1], "right": p[3]}

    def p_register_func(self, p):
        """
        registerFunc    : NOT register
                        | MINUS register
        """

        p[0] = {"op": p[1], "value": p[2]}
    
    def p_register_num(self, p):
        """
        registerNum     : register PLUS num
                        | register MINUS num
        """

        p[0] = {"op": p[2], "left": p[1], "right": p[3]}

    def p_num(self, p):
        """
        num : NUMBER
        """
        if p[1] in [0, 1]:
            p[0] = p[1]
        else:
            print("Value Error : The only available values are 1, 0, and -1.")
            p[0] = 0

    def p_minus_num(self, p):
        """
        num        : MINUS NUMBER
        """
        if p[2] == 1:
            p[0] = - p[2]

        else:
            print("Value Error : The only available values are 1, 0, and -1.")
            p[0] = 0

    
    
    def p_register(self, p):
        """
        register    : A
                    | M
                    | D
        """
        p[0] = str(p[1])
    
    
    def p_jump(self, p):
        """
        jump    : JGT
                | JEQ
                | JGE
                | JLT
                | JNE
                | JLE
                | JMP
        """
        p[0] = p[1]
    

    def eval_comp(self, node): # comp 評価関数

        # レジスタ単体
        if isinstance(node, str):
            if node == "A":
                return self.registers["A"]
            if node == "D":
                return self.registers["D"]
            if node == "M":
                return self.ram[self.registers["A"]]

        # 数字
        if isinstance(node, int):
            return node

        # 単項
        if ("op" in node) and ("value" in node):
            val = self.eval_comp(node["value"])
            if node["op"] == "!":
                return (~val) & 0xFFFF
            if node["op"] == "-":
                return -val

        # 二項
        if "op" in node:
            left = self.eval_comp(node["left"])
            right = self.eval_comp(node["right"])
            op = node["op"]

            if op == "+":
                return (left + right) & 0xFFFF
            if op == "-":
                return (left - right) & 0xFFFF
            if op == "&":
                return (left & right) & 0xFFFF
            if op == "|":
                return (left | right) & 0xFFFF

        raise Exception("Unknown comp node: " + str(node))
    

if __name__ == "__main__":
    if len(argv) < 2:
        file = "main.asm"
    else:
        file = argv[1]

    with open(file, "r", encoding="UTF-8") as source:
        program = source.read()

    with HackCodeAnalyze(program, debug = False) as l:
        # print(l)
        result = l.parse()
    
    # .hack
    input("終了")