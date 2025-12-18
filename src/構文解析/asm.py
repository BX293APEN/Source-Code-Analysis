from ply import lex, yacc
from sys import argv, exit
import os

class HackCodeAnalyze:
    """オブジェクトの説明
| method | args | description |
| - | - | - |
| .__init__ | code | codeの中に解析するコードの文字列を入れる |
| .set_code | code | codeの中に解析するコードの文字列を入れる |
| .build | **kwargs | lexにオブジェクトを認識させる(ブロック構文で自動実行) |
| .get_tokens | - | lexで字句解析をし、トークン化する |
| .parse | - | YACCで構文解析をし、トークン化する |
| .asm | - | Hackアセンブリ化したコードをリストで返す |
    """

    def set_code(
        self,
        code                    = ""
    ):
        self.code               = code

    def build(self, **kwargs):
        self.lexer              = lex.lex(
            module              = self, 
            **kwargs
        )
        
        self.yacc               = yacc.yacc(
            module              = self, 
            **kwargs
        )
    
    def parse(self): # yacc による構文解析
        return self.yacc.parse(
            self.code, 
            lexer               = self.lexer
        )
    
    def get_tokens(self):
        self.lexer.input(self.code)
        self.sourceTokenList    = []
        while True:
            tok                 = self.lexer.token()
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
        code                    = "", 
        debug                   = True
    ):
        self.debug              = debug
        self.set_code(code)

        self.varTable           = {
            "SP"                : 0, 
            "LCL"               : 1, 
            "ARG"               : 2, 
            "THIS"              : 3, 
            "THAT"              : 4,
            "SCREEN"            : 16384, 
            "KBD"               : 24576
        }

        self.reservedVars       = [
            "SP", 
            "LCL", 
            "ARG", 
            "THIS", 
            "THAT",
            "SCREEN", 
            "KBD"
        ]
        
        self.registerNum        = 16
        for i in range(self.registerNum):
            self.varTable[f"R{i}"] = i
            self.reservedVars.append(f"R{i}")

        self.nextVarAddr        = self.registerNum
        self.pc = 0

        self.t_ignore           = ' \t'     # A string containing ignored characters (spaces and tabs)
        self.t_ignore_comment   = r'//.*'

        self.reservedWords      = (
            "AMD",
            "ADM",
            "AD", 
            "AM", 
            "MD", 
            "DM",
            "A", 
            "M", 
            "D", 
            "JGT", 
            "JEQ", 
            "JGE", 
            "JLT", 
            "JNE", 
            "JLE", 
            "JMP"
        )

        self.tokens             = (         # tokensの要素に t_を付けると定義可能
            "AT",       # "@"
            "LPAREN",   # "("
            "RPAREN",   # ")"
            "EQUAL",    # "="
            "SEMI",     # ";"
            "PLUS",     # "+"
            "MINUS",    # "-"
            "AND",      # "&"
            "OR",       # "|"
            "NOT",      # "!"
            "NUMBER",
            "SYMBOL",

        ) + self.reservedWords
        
        
        self.t_AT               = r'@'
        self.t_LPAREN           = r'\('
        self.t_RPAREN           = r'\)'
        self.t_EQUAL            = r'='
        self.t_SEMI             = r';'
        self.t_PLUS             = r'\+'
        self.t_MINUS            = r'-'
        self.t_AND              = r'&'
        self.t_OR               = r'\|'
        self.t_NOT              = r'!'

    
    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno          += len(t.value)

    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # A regular expression rule with some action code
    # Note addition of self parameter since we're in a class
    def t_NUMBER(self, t):
        r'\d+'
        t.value                 = int(t.value)
        return t
    
    def t_SYMBOL(self, t):
        r'[A-Za-z_\.\$:][A-Za-z0-9_\.\$:]*'
        if t.value in self.reservedWords:
            t.type              = t.value
        return t
    


    # 構文解析
    def p_error(self, p):
        print("Syntax error at", p)

    def p_statements(self, p):
        """
        statements  : statement statements
                    | empty
        """
        if len(p)               == 3:
            p[0]                = [p[1]] + p[2]
        else:
            p[0]                = []

    def p_empty(self, p):
        "empty : "

    def p_statement_a(self, p):
        "statement  : a_instruction"
        p[0]                    = p[1]
        if self.debug:
            print("A命令")
        
        self.pc += 1
    
    def p_statement_l(self, p):
        "statement  : l_instruction"
        p[0]                    = p[1]
        if self.debug:
            print("Label")
    
    def p_statement_c(self, p):
        "statement  : c_instruction"
        p[0]                    = p[1]
        if self.debug:
            print("C命令")
        
        self.pc += 1

    
    def get_next_addr(self):
        value = None
        if self.nextVarAddr     < self.varTable["SCREEN"]:
            value               = self.nextVarAddr
        self.nextVarAddr += 1
        return value

    # A命令
    def p_a_instruction(self, p):
        """
        a_instruction   : AT SYMBOL
                        | AT NUMBER
        """
        if isinstance(p[2], int):
            value               = p[2]
            if self.debug:
                print(f"0{value:015b}")
            p[0]                = {
                "instruction"   : "A", 
                "type"          : f"{p.slice[2].type}", 
                "code"          : f"0{value:015b}", 
                "at"            : str(p[2])
            }
        else:
            label               = str(p[2])
            if label in self.varTable.keys():
                value           = self.varTable[label]
                p[0]            = {
                    "instruction": "A", 
                    "type": f"{p.slice[2].type}", 
                    "code" : f"0{value:015b}", 
                    "at" : str(p[2])
                }
            else:
                self.varTable[label] = -1 # 不定フラグ
                p[0]            = {
                    "instruction": "A", 
                    "type": f"{p.slice[2].type}", 
                    "code" : f"pending", 
                    "at" : str(p[2])
                }

    # L命令 (LABEL)
    def p_l_instruction(self, p):
        """
        l_instruction : LPAREN SYMBOL RPAREN
        """
        label                   = p[2]
        if label not in self.reservedVars:
            self.varTable[label] = self.pc

        p[0]                    = {
            "instruction": "L", 
            "label": label
        }

    #   C 命令
    # dest=comp;jump
    def p_c_instruction_1(self, p):
        """
        c_instruction   : dest EQUAL comp SEMI jump
                        | comp SEMI jump
                        | dest EQUAL comp
                        | comp
        
        """

        dest                    = dict()
        dest["code"]            = "000"
        comp                    = None
        jump                    = dict()
        jump["code"]            = "000"

        if len(p)               == 2:
            comp                = p[1]
        elif (
            (len(p)             == 4 ) and 
            (p.slice[2].type    == "SEMI")
        ):
            comp                = p[1]
            jump                = p[3]
        elif (
            (len(p)             == 4) and 
            (p.slice[2].type    == "EQUAL")
        ):
            dest                = p[1]
            comp                = p[3]
        elif len(p)             == 6:
            dest                = p[1]
            comp                = p[3]
            jump                = p[5]
        
        cCode                   = f"111{comp["code"]}{dest["code"]}{jump["code"]}"

        p[0]                    = {
            "instruction"       : "C",
            "dest"              : dest,
            "comp"              : comp,
            "jump"              : jump,
            "code"              : cCode
        }


    def p_dest(self, p):
        """
        dest    : AMD
                | ADM
                | AD
                | AM
                | MD 
                | DM
                | A
                | M
                | D
        """

        destCode                = 0b000
        if "A" in str(p[1]):
            destCode            |= 0b100
        if "D" in str(p[1]):
            destCode            |= 0b010
        if "M" in str(p[1]):
            destCode            |= 0b001
        
        destCode                = f"{destCode:03b}"
        p[0]                    = {
            "value"             : str(p[1]),
            "code"              : destCode
        }

    def p_comp_1(self, p):      # 2項演算
        """
        comp        : registers
                    | registerNum
                    | registerFunc
        """
        p[0]                    = p[1]
    
    def p_comp_2(self, p):      # 単項演算
        """
        comp        : register
                    | num
        """

        code                    = f"{str(p[1])}"

        monomialPattern         = {
            # a == 0
            "0"                 : "0101010",
            "1"                 : "0111111",
            "-1"                : "0111010",
            "D"                 : "0001100",
            "A"                 : "0110000",

            # a == 1
            "M"                 : "1110000",
        }

        if code not in monomialPattern.keys():
            raise f"Syntax Error : {code} Unknown"

        p[0]                    = {
            "value"             : code,
            "code"              : monomialPattern["code"]
        }
    
    def p_registers(self, p):
        """
        registers       : register PLUS register
                        | register MINUS register
                        | register AND register
                        | register OR register
        """

        code                    = f"{str(p[1])}{str(p[2])}{str(p[3])}"

        registersPattern        = {
            # a == 0
            "D+A": "0000010",
            "D-A": "0010011",
            "A-D": "0000111",
            "D&A": "0000000",
            "D|A": "0010101",

            # a == 1
            "D+M": "1000010",
            "D-M": "1010011",
            "M-D": "1000111",
            "D&M": "1000000",
            "D|M": "1010101",
        }

        if code not in registersPattern.keys():
            raise f"Syntax Error : {code} Unknown"
        
        p[0]                    = {
            "op"                : p[2], 
            "left"              : p[1], 
            "right"             : p[3],
            "code"              : registersPattern[code]
        }

    def p_register_func(self, p):
        """
        registerFunc    : NOT register
                        | MINUS register
        """

        code                    = f"{str(p[1])}{str(p[2])}"

        registerFuncPattern     = {
            # a == 0
            "!D"                : "0001101",
            "!A"                : "0110001",
            "-D"                : "0001111",
            "-A"                : "0110011",

            # a == 1
            "!M"                : "1110001",
            "-M"                : "1110011",
        }

        if code not in registerFuncPattern.keys():
            raise f"Syntax Error : {code} Unknown"

        p[0]                    = {
            "op"                : p[1], 
            "value"             : p[2],
            "code"              : registerFuncPattern[code]
        }
    
    def p_register_num(self, p):
        """
        registerNum     : register PLUS num
                        | register MINUS num
        """

        code                    = f"{str(p[1])}{str(p[2])}{str(p[3])}"
        
        registerNumPattern      = {
            # a == 0
            "D+1"               : "0011111",
            "A+1"               : "0110111",
            "D-1"               : "0001110",
            "A-1"               : "0110010",

            # a == 1
            "M+1"               : "1110111",
            "M-1"               : "1110010",
        }

        if code not in registerNumPattern.keys():
            raise f"Syntax Error : {code} Unknown"

        p[0]                    = {
            "op"                : p[2], 
            "left"              : p[1], 
            "right"             : p[3],
            "code"              : registerNumPattern[code]
        }

    def p_num(self, p):
        """
        num : NUMBER
        """
        if p[1] in [0, 1]:
            p[0]                = p[1]
        else:
            print("Value Error : The only available values are 1, 0, and -1.")
            p[0]                = 0

    def p_minus_num(self, p):
        """
        num        : MINUS NUMBER
        """
        if p[2]                 == 1:
            p[0]                = - p[2]

        else:
            print("Value Error : The only available values are 1, 0, and -1.")
            p[0]                = 0

    
    
    def p_register(self, p):
        """
        register    : A
                    | M
                    | D
        """
        p[0]                    = str(p[1])
    
    
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

        jumpPattern             = {
            "JGT"               : "001",
            "JEQ"               : "010",
            "JGE"               : "011",
            "JLT"               : "100",
            "JNE"               : "101",
            "JLE"               : "110",
            "JMP"               : "111"
        }

        jumpCode                = dict()
        jumpCode["type"]        = str(p[1])



        if jumpCode["type"] not in jumpPattern.keys():
            raise f"Syntax Error : {jumpCode["type"]} Unknown"
        
        jumpCode["code"]        = jumpPattern[jumpCode["type"]]
        
        p[0] = jumpCode

    
    def asm(self):
        """
        .hack 用の 16bit バイナリを list で返す
        """

        out = []
        for i in self.parse():
            if i["instruction"]     == "A":
                if i["type"]        == "NUMBER":
                    out.append(i["code"])
                else:
                    if (
                        (i["code"]              == "pending") and 
                        (self.varTable[i["at"]] == -1)
                    ):
                        addr = self.get_next_addr()
                        if addr is not None:
                            self.varTable[i["at"]] = addr
                        else: 
                            self.varTable[i["at"]] = 0
                    out.append(f"0{self.varTable[i["at"]]:015b}")

            elif i["instruction"]   == "C":
                out.append(i["code"])

        return out
    

if __name__ == "__main__":
    debug = False

    if len(argv)    < 2:
        file        = "main.asm"
    else:
        file        = argv[1]

    with open(file, "r", encoding="UTF-8") as source:
        program     = source.read()

    with HackCodeAnalyze(program, debug = debug) as l:
        # print(l)
        result      = l.asm()
    
    dirName         = os.path.dirname(file)
    buildDir        = f"{dirName}/build"
    os.makedirs(buildDir, exist_ok=True)

    baseName        = os.path.splitext(os.path.basename(file))[0]  # ファイル名だけ取り出す
    hackFile        = os.path.join(buildDir, f"{baseName}.hack")

    with open(hackFile, "w", encoding="UTF-8") as f:
        f.write("")
    
    with open(hackFile, "a", encoding="UTF-8") as f:
        for r in result:
            print(r, file = f)
            if (debug):
                print(r)
        
    input("終了")