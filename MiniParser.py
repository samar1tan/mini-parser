import sys
import traceback
from treelib import Tree
from mini_scanner import MiniScanner


def find_last(string, word):
    index = string.find(word)
    index_ = 0
    while True:
        try:
            index_ = string.find(word, index + len(word))
        except:
            return index
        else:
            if index_ == -1:
                return index
            else:
                index = index_


class MiniParser:
    def __init__(self, scanner):
        """ parser主程序，作为唯一的入口、正常出口以及出错处理出口 """
        assert type(scanner) == MiniScanner
        self.scanner = scanner
        self.ast = Tree()
        self.ast.create_node('start', 'start')
        self.temp_cnt = 0
        self.temp_name = 'start'

        end = 0  # parse中合法的最后一个Token的序号，若accepted则指向‘#’
        try:  # 出错处理基于Python自建的异常机制
            end = self.parse_source(0)
        except Exception as e:
            # 出错处理
            traceback.print_exc()  # 打印traceback信息，内含出错时正在parse的文法成分及预计的合法token
            error_msg = self.get_error_msg(e.args[0])  # 打印非法token的相关信息
            sys.exit(error_msg)
        else:
            if end == len(self.tokens) - 1:  # token串完全合法
                self.ast.show()
                print('accepted')
            else:
                # token串末尾出现非法token，补充进行出错处理
                error_msg = self.get_error_msg(end)
                sys.exit(error_msg)

    def __getattr__(self, name):
        try:
            return getattr(self.scanner, name)
        except:
            try:
                return getattr(self, name)
            except:
                sys.exit('attribute error')

    def get_unique_name(self, prefix):
        self.temp_cnt += 1
        self.temp_name = prefix + str(self.temp_cnt)

    def parser(parser_func):
        def wrapper(self, idx, symbol=None):
            parent_name = self.temp_name
            raw_child_name = parser_func.__name__
            pos = raw_child_name.find('_')
            child_name = raw_child_name[pos+1:]
            self.get_unique_name(child_name)
            self.ast.create_node(child_name, self.temp_name, parent=parent_name)

            if symbol:
                result = parser_func(self, idx, symbol)
            else:
                result = parser_func(self, idx)

            self.temp_name = parent_name
            return result
        return wrapper

    @parser
    def parse_source(self, idx=0):
        """ parse <Source> """
        while idx < len(self.tokens):
            if self.tokens[idx][1] in self.reserved or self.tokens[idx][0] == self.identifier_id:
                idx = self.parse_statement(idx)
            else:
                break
        return idx

    def get_error_msg(self, idx):
        """ 生成非法Token的内容、位置信息 """
        wrong_token = self.tokens[idx]  # 获取非法token
        # 获取非法token对应的字符串
        if wrong_token[0] == self.constant_id:
            wrong_word = self.constant_table[wrong_token[1]]
        elif wrong_token[0] == self.identifier_id:
            wrong_word = self.identifier_table[wrong_token[1]]
        else:
            wrong_word = wrong_token[1]

        # 获取非法token所在的位置：行号（line_num）和列号（column_num）
        line_num = wrong_token[2]
        line = self.source.split('\n')[line_num - 1]
        column_num = find_last(line, wrong_word)

        # 生成报错信息
        error_msgs = []
        sources = self.source.split('\n')
        error_msgs.append('{0}: {1}'.format(line_num, sources[line_num-1]))  # 打印非法token所在行
        # 指示非法token在源码中的位置
        msg = ''
        start_bias = len(str(line_num)) + 2
        for _ in range(start_bias + column_num):
            msg += ' '
        error_msgs.append(msg + '^')
        error_msgs.append('错误: 在源文件第{0}行发现非法Token\'{1}\''.format(line_num, wrong_word))
        return '\n'.join(error_msgs)

    def check(self, idx, advance=1):
        if idx + advance > len(self.tokens):
            self.get_error_msg(len(self.tokens) - 1)
        # print(self.tokens[idx])

    @parser
    def parse_statement(self, idx):
        """ parse <Statement> """
        self.check(idx)
        if self.tokens[idx][0] == self.identifier_id:
            idx = self.parse_assignment(idx)
        elif self.tokens[idx][1] == 'if':
            idx = self.parse_if(idx)
        elif self.tokens[idx][1] == 'while':
            idx = self.parse_while(idx)
        elif self.tokens[idx][0] > self.reserved_id + 2:
            idx = self.parse_definition(idx)
        else:
            raise Exception(idx)
        return idx

    @parser
    def parse_identifier(self, idx):
        self.check(idx)
        if self.tokens[idx][0] != self.identifier_id:
            raise Exception(idx)
        else:
            identifier = None
            identifier_num = self.tokens[idx][1]
            for i in self.identifier_table:
                if i[0] == identifier_num:
                    identifier = i[1]
                    break
            self.temp_cnt += 1
            child_name = identifier + str(self.temp_cnt)
            self.ast.create_node(identifier, child_name, parent=self.temp_name)
            return idx + 1

    @parser
    def parse_constant(self, idx):
        self.check(idx)
        if self.tokens[idx][0] != self.constant_id:
            raise Exception(idx)
        else:
            constant = None
            constant_num = self.tokens[idx][1]
            for i in self.constant_table:
                if i[0] == constant_num:
                    constant = i[1]
                    break
            constant = str(constant)
            self.temp_cnt += 1
            child_name = constant + str(self.temp_cnt)
            self.ast.create_node(constant, child_name, parent=self.temp_name)
            return idx + 1

    @parser
    def parse_symbol(self, idx, symbol):
        self.temp_cnt += 1
        child_name = symbol + str(self.temp_cnt)
        self.ast.create_node(symbol, child_name, parent=self.temp_name)
        self.check(idx)
        if self.tokens[idx][1] != symbol:
            raise Exception(idx)
        else:
            return idx + 1

    # parse_expr系列 ###
    @parser
    def parse_expression(self, idx):
        """ parse <表达式>，对各种表达式如<逻辑与式>的parse过程类似 """
        self.check(idx)
        idx = self.parse_and(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] == '||':
                idx = self.parse_and(idx + 1)
        return idx

    @parser
    def parse_and(self, idx):
        self.check(idx)
        idx = self.parse_bitwise_or(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] == '&&':
                idx = self.parse_bitwise_or(idx + 1)
        return idx

    @parser
    def parse_bitwise_or(self, idx):
        self.check(idx)
        idx = self.parse_bitwise_nor(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] == '|':
                idx = self.parse_bitwise_nor(idx + 1)
        return idx

    @parser
    def parse_bitwise_nor(self, idx):
        self.check(idx)
        idx = self.parse_bitwise_and(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] == '^':
                idx = self.parse_bitwise_and(idx + 1)
        return idx

    @parser
    def parse_bitwise_and(self, idx):
        self.check(idx)
        idx = self.parse_equal(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] == '&':
                idx = self.parse_equal(idx + 1)
        return idx

    @parser
    def parse_equal(self, idx):
        self.check(idx)
        idx = self.parse_compare(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] in ['==', '!=']:
                idx = self.parse_compare(idx + 1)
        return idx

    @parser
    def parse_compare(self, idx):
        self.check(idx)
        idx = self.parse_add(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] in ['<=','>=','<','>']:
                idx = self.parse_add(idx + 1)
        return idx

    @parser
    def parse_add(self, idx):
        self.check(idx)
        idx = self.parse_multiply(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] in ['+', '-']:
                idx = self.parse_multiply(idx + 1)
        return idx

    @parser
    def parse_multiply(self, idx):
        self.check(idx)
        idx = self.parse_bracket(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] in ['*','/','%']:
                idx = self.parse_bracket(idx + 1)
        return idx
    # 系列结束 ###

    @parser
    def parse_bracket(self, idx):
        self.check(idx)
        if self.tokens[idx][1] == '(':
            idx = self.parse_expression(idx + 1)
            idx = self.parse_symbol(idx, ')')
        elif self.tokens[idx][0] == self.identifier_id:
            idx = self.parse_identifier(idx)
        elif self.tokens[idx][0] == self.constant_id:
            idx = self.parse_constant(idx)
        else:
            raise Exception(idx)
        return idx

    @parser
    def parse_assignment(self, idx):
        """ parse <Assignment> """
        self.check(idx, 4)
        idx = self.parse_assignment_util(idx)
        idx = self.parse_symbol(idx, ';')
        return idx

    @parser
    def parse_assignment_util(self, idx):
        idx = self.parse_identifier(idx)
        idx = self.parse_symbol(idx, '=')
        if self.tokens[idx][0] == self.identifier_id and self.tokens[idx+1][1] == ';':
            idx = self.parse_identifier(idx)
        elif self.tokens[idx][0] == self.identifier_id and self.tokens[idx+1][1] == '=':
            idx = self.parse_assignment_util(idx)
        else:
            idx = self.parse_expression(idx)
        return idx

    @parser
    def parse_block(self, idx):
        """ parse <Block> """
        self.check(idx)
        if self.tokens[idx][1] == '{':
            idx = self.parse_source(idx + 1)
            idx = self.parse_symbol(idx, '}')
        else:
            idx = self.parse_statement(idx)
        return idx

    @parser
    def parse_if(self, idx):
        """ parse <If> """
        self.check(idx, 5)
        idx = self.parse_symbol(idx+1, '(')
        idx = self.parse_expression(idx)
        idx = self.parse_symbol(idx, ')')
        idx = self.parse_block(idx)
        if idx < len(self.tokens):
            if self.tokens[idx][1] == 'else':
                idx = self.parse_block(idx+1)
        return idx

    @parser
    def parse_definition(self, idx):
        self.check(idx, 3)
        type = self.tokens[idx][1]
        self.temp_cnt += 1
        child_name = type + str(self.temp_cnt)
        self.ast.create_node(type, child_name, parent=self.temp_name)
        if self.tokens[idx+2][1] == '=':
            idx = self.parse_assignment(idx + 1)
        else:
            idx = self.parse_identifier(idx+1)
            idx = self.parse_symbol(idx, ';')
        return idx

    @parser
    def parse_while(self, idx):
        """ parse <While> """
        self.check(idx, 5)
        idx = self.parse_symbol(idx+1, '(')
        idx = self.parse_expression(idx)
        idx = self.parse_symbol(idx, ')')
        idx = self.parse_block(idx)
        return idx


if __name__ == '__main__':
    parser = MiniParser(MiniScanner('test.txt'))
