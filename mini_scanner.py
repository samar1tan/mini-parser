import os


class MiniScanner:
    ###### CONSTANT ######
    symbols = ['#', '+', '-', '*', '/', '%', '=',
               '(', ')', '{', '}', '>', '<', ';',
               '^', '!', '&', '|', '%', '==', '!=',
               '>=', '<=', '&&', '||']
    reserved = ['if', 'else', 'while', 'int',
                'float', 'double', 'bool']
    reserved_id = len(symbols)
    constant_id = len(symbols) + len(reserved)
    identifier_id = constant_id + 1
    ###### CONSTANT ######

    ###### PROPERTY ######
    source = None
    errors = None
    tokens = []
    constant_table = []
    identifier_table = []

    ###### PROPERTY ######

    def __init__(self, file):
        self.read(file)
        self.scan_fa()

    def read(self, file):
        """read code from file and preprocess"""
        source = []
        with open(file, encoding='utf-8') as fp:
            for line in fp.readlines():
                comment_index = line.find('//')  # remove comments
                if comment_index < 0:
                    source.append(line.strip())
                elif comment_index == 0:
                    source.append(' ')  # full-line comment, to preserve original line number
                elif comment_index > 0:
                    source.append(line[:comment_index].strip())
        self.source = '\n'.join(source)
        return '\n'.join(['%2d: %s' % (i + 1, line) for i, line in enumerate(source)])

    def scan_fa(self):
        """scan for tokens in FA's perspective"""
        source = self.source
        i = 0
        self.line = 1
        while i < len(source):
            if source[i] in self.symbols:  # is symbol
                ret, i = self.scan_symbol(i)
                if ret == 1:
                    return
            elif source[i].isalpha():  # is alphabet
                ret, i = self.scan_identifier(i)
                if ret != 0:
                    print(self.errors)
                    os._exit(1)
                    return
            elif source[i].isdecimal():  # is decimal
                ret, i = self.scan_decimal(i)
                if ret != 0:
                    print(self.errors)
                    os._exit(1)
                    return
            elif source[i] == ' ':  # just space
                i += 1
            elif source[i] == '\n':
                i += 1
                self.line += 1
            else:  # unexpected
                self.errors = 'ERROR: unexpected token \'%s\' in line %d: %s' \
                              % (source[i], self.line, self.source.split('\n')[self.line - 1])
                print(self.errors)
                os._exit(1)
                return

    def scan_symbol(self, index):
        """
        scan for symbols
        ret: 1 if it's end of the source code else 0
        """
        ret = 0
        source = self.source
        token = source[index]
        if token == '#':  # end of the source code
            self.tokens.append((self.symbols.index(token), token, self.line))
            ret = 1
            return ret, index
        # check for longer symbols
        if source[index + 1] in self.symbols:
            token += source[index + 1]
        if token not in self.symbols:
            token = token[0]
        self.tokens.append((self.symbols.index(token), token, self.line))
        return ret, index + len(token)

    def scan_decimal(self, index):
        """
        scan for decimals
        ret:  0 if nothing goes wrong
             -1 if multiple decimal points in one constant
             -2 if decimal ends with alphabet
        """
        ret = 0
        decimal_point = False
        source = self.source
        token = source[index]
        for i in range(index + 1, len(source)):
            if source[i].isdecimal():
                token += source[i]
            elif source[i] == '.':
                token += source[i]
                if decimal_point:  # multiple decimal points
                    ret = -1
                    self.errors = 'ERROR: multiple decimal points in one constant \'%s\'' % token
                    break
                else:  # the first decimal point
                    decimal_point = True
            else:
                break
        if source[i].isalpha():  # check if decimal ends with alphabet
            ret = -2
            self.errors = 'ERROR: decimal ends with alphabet \'%s\'' % (token + source[i])
            return ret, i
        constant_set = [x[1] for x in self.constant_table]
        if token in constant_set:  # check constant table
            constant_index = constant_set.index(token)
        else:  # it's a new constant
            constant_index = len(self.constant_table)
            self.constant_table.append((constant_index, token))
        self.tokens.append((self.constant_id, constant_index, self.line))
        return ret, i

    def scan_identifier(self, index):
        """
        scan for identifiers
        ret: -1 if met invalid identifier else 0
        """
        ret = 0
        source = self.source
        token = source[index]
        for i in range(index + 1, len(source)):
            if source[i].isalpha() or source[i].isdecimal():
                token += source[i]
            else:
                break
        if token in self.reserved:  # check in reserved keywords table
            self.tokens.append((self.reserved_id + self.reserved.index(token), token, self.line))
        else:
            symbol_set = [x[1] for x in self.identifier_table]
            if token in symbol_set:  # existing identifier
                token_index = symbol_set.index(token)
                self.tokens.append((self.identifier_id, token_index, self.line))
            elif self.is_valid(token):  # new identifier
                symbol_index = len(self.identifier_table)
                self.tokens.append((self.identifier_id, symbol_index, self.line))
                self.identifier_table.append((symbol_index, token))
            else:  # invalid token
                self.errors = 'ERROR: \'%s\' is not a valid identifier' % token
                ret = -1
        return ret, i

    @staticmethod
    def is_valid(token):
        """validate token"""
        return not token[0].isdecimal()


if __name__ == '__main__':
    scanner = MiniScanner('test.txt')
    print('tokens:', scanner.tokens)
    print('constant:%s' % (scanner.constant_table))
    print('identifier:%s' % (scanner.identifier_table))