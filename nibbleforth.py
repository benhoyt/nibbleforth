"""Nibbleforth - the world's most compact stack machine (Forth) bytecode

This is just some source code I started to test some ideas. Don't have time to
work on it further at this point. Posting this on GitHub for the record.

Currently this source code only parses and interprets a very limited subset of
Forth, and is able to print out the frequencies of each word used, including
jump, conditional jump, and literal instructions.

See README.md for more details about how this would actually work.

"""

import collections
import msvcrt
import operator
import os
import re
import sys

stack = []
def push(x): stack.append(x)
def pop(): return stack.pop()

mem = [0] * 100
def fetch(): push(mem[pop()])
def store(): a = pop(); mem[a] = pop()

def dup(): x = pop(); push(x); push(x)
def swap(): x = pop(); y = pop(); push(x); push(y)
def drop(): pop()

def abortq():
    s = pop()
    if pop():
        print >>sys.stderr, s
        sys.exit(1)
def key():
    c = ord(msvcrt.getch())
    if c == 27:
        print >>sys.stderr, 'exiting'
        sys.exit(1)
    push(c)
def emit(): sys.stdout.write(chr(pop()))
def cr(): sys.stdout.write('\n')
def dot(): sys.stdout.write(str(pop()))

def plus(): push(pop() + pop())
def minus(): n = pop(); push(pop() - n)
def star(): push(pop() * pop())
def slash(): n = pop(); push(pop() // n)
def or_(): push(pop() | pop())
def negate(): push(-pop())

def zeroequals(): push(pop() == 0)
def uless(): n = pop(); push(0 <= pop() < n)
def equals(): push(pop() == pop())
def notequals(): push(pop() != pop())

primitives = {
    '@': fetch,
    '!': store,
    'dup': dup,
    'swap': swap,
    'drop': drop,
    'abort"': abortq,
    'key': key,
    'emit': emit,
    'cr': cr,
    '.': dot,
    '+': plus,
    '-': minus,
    '*': star,
    '/': slash,
    'or': or_,
    'negate': negate,
    '0=': zeroequals,
    'u<': uless,
    '=': equals,
    '<>': notequals,
}

def run(wordlist, program):
    pc = 0
    while True:
        op = program[pc]
        pc += 1
        if op == 'exit':
            return
        elif op == 'jz':
            offset = pop()
            if pop() == 0:
                pc += offset
            continue
        elif op == 'jmp':
            offset = pop()
            pc += offset
            continue

        if isinstance(op, int):
            push(op)
        elif isinstance(op, str) and op.startswith('__s"'):
            push(op[4:-1])
        elif op in wordlist:
            run(wordlist, wordlist[op])
        elif op in primitives:
            primitives[op]()
        else:
            raise Exception('unknown op: {0!r}'.format(op))

class CompileError(Exception):
    def __init__(self, msg, filename, line_num):
        self.msg = msg
        self.filename = os.path.split(filename)[1]
        self.line_num = line_num

    def __str__(self):
        return '{0}:{1}: {2}'.format(self.filename, self.line_num, self.msg)

class Compiler(object):
    word_re = re.compile(r'(\s+)')

    def __init__(self, filename):
        self.filename = filename
        self.compiling = False
        self.line_num = 1
        self.definition_name = None
        self.definition = []
        self.wordlist = {}
        self.noname_num = 0
        self.control_stack = []
        self.here = 0

    def parse(self):
        with open(self.filename) as f:
            for line in f:
                self.parse_line(line)
                self.line_num += 1

    def run(self, word):
        run(self.wordlist, self.wordlist[word])

    @classmethod
    def parse_int(cls, s, base=10):
        try:
            return int(s, base)
        except ValueError:
            return None

    def parse_line(self, line):
        words = self.word_re.split(line)
        self.it = iter(words)
        for word in self.it:
            if not word or word.isspace():
                continue
            word = word.lower()
            if word in self.immediates:
                self.immediates[word](self)
            elif self.compiling:
                if word.startswith('$'):
                    int_value = self.parse_int(word[1:], base=16)
                else:
                    int_value = self.parse_int(word)
                word = int_value if int_value is not None else word
                self.compile(word)

    def get_frequencies(self):
        freqs = collections.defaultdict(int)
        for definition in self.wordlist.itervalues():
            for word in definition:
                freqs[word] += 1
        return sorted(freqs.iteritems(), key=operator.itemgetter(1, 0))

    def get_word(self):
        self.it.next()  # eat whitespace "token"
        return self.it.next()

    def get_string(self, delim='"'):
        pieces = []
        space = self.it.next()[1:]  # skip one space
        if space:
            pieces.append(space)
        while True:
            piece = self.it.next()
            delim_pos = piece.find(delim)
            if delim_pos >= 0:
                last_piece = piece[:delim_pos]
                if last_piece:
                    pieces.append(last_piece)
                break
            pieces.append(piece)
        return ''.join(pieces)

    def error(self, msg):
        return CompileError(msg, self.filename, self.line_num)

    def compile(self, word):
        self.definition.append(word)

    def backslash(self):
        for word in self.it:
            pass

    def paren(self):
        for word in self.it:
            if word == ')':
                break

    def colon(self, name=None):
        if self.compiling:
            raise self.error("can't use ':' when already in a colon definition")
        self.compiling = True
        self.definition_name = self.get_word() if name is None else name
        self.definition = []

    def colon_noname(self):
        self.noname_num += 1
        name = 'noname{0}'.format(self.noname_num)
        self.colon(name=name)

    def semicolon(self):
        if not self.compiling:
            raise self.error("can't use ';' outside of a colon definition")
        if self.control_stack:
            raise self.error('control structure mismatch')
        self.compiling = False
        self.compile('exit')
        self.wordlist[self.definition_name] = self.definition
        print ':', self.definition_name
        print '   ', ' '.join(repr(x) for x in self.definition)

    def left_bracket(self):
        if not self.compiling:
            raise self.error("can't use '[' outside of a colon definition")
        self.compiling = False

    def right_bracket(self):
        if self.compiling:
            raise self.error("can't use ']' when compiling")
        self.compiling = True

    def bracket_tick(self):
        name = self.get_word()
        self.compile('&' + name)

    def jump_forward(self, opcode):
        self.compile(None)
        self.compile(opcode)
        self.control_stack.append(('forward', len(self.definition)))

    def resolve_forward(self, stack_index=0):
        if not self.control_stack:
            raise self.error('control structure mismatch')
        direction, offset = self.control_stack.pop(len(self.control_stack) - 1 - stack_index)
        if direction != 'forward':
            raise self.error('control structure mismatch')
        delta = len(self.definition) - offset
        self.definition[offset - 2] = delta

    def mark_reverse(self):
        self.control_stack.append(('reverse', len(self.definition)))

    def resolve_reverse(self, opcode, stack_index=0):
        if not self.control_stack:
            raise self.error('control structure mismatch')
        direction, offset = self.control_stack.pop(len(self.control_stack) - 1 - stack_index)
        if direction != 'reverse':
            raise self.error('control structure mismatch')
        delta = offset - len(self.definition) -  2
        self.compile(delta)
        self.compile(opcode)

    def if_(self):
        self.jump_forward('jz')

    def else_(self):
        self.jump_forward('jmp')
        self.resolve_forward(1)

    def then(self):
        self.resolve_forward()

    def begin(self):
        self.mark_reverse()

    def while_(self):
        if not self.control_stack:
            raise self.error('control structure mismatch')
        self.jump_forward('jz')
        top = self.control_stack.pop()
        second = self.control_stack.pop()
        self.control_stack.append(top)
        self.control_stack.append(second)

    def repeat(self):
        self.resolve_reverse('jmp')
        self.resolve_forward()

    def until(self):
        self.resolve_reverse('jz')

    def again(self):
        self.resolve_reverse('jmp')

    def s_quote(self):
        if not self.compiling:
            return
        s = self.get_string()
        self.compile('__s"{0}"'.format(s))

    def abort_quote(self):
        self.s_quote()
        self.compile('abort"')

    def bracket_char(self):
        ch = self.get_word()
        self.compile(ord(ch))

    def postpone(self):
        self.compile('&' + self.get_word())
        self.compile('compile')

    def variable(self):
        name = self.get_word()
        address = self.here
        def var_address(self):
            self.compile(address)
        self.immediates[name] = var_address
        self.here += 1

    immediates = {
        '\\': backslash,
        '\\g': backslash,
        '(': paren,
        ':': colon,
        ':noname': colon_noname,
        ';': semicolon,
        '[': left_bracket,
        ']': right_bracket,
        "[']": bracket_tick,
        'if': if_,
        'else': else_,
        'then': then,
        'endif': then,
        'begin': begin,
        'while': while_,
        'repeat': repeat,
        'until': until,
        'again': again,
        's"': s_quote,
        'abort"': abort_quote,
        '[char]': bracket_char,
        'postpone': postpone,
        'variable': variable,
    }

if __name__ == '__main__':
    compiler = Compiler(sys.argv[1])
    compiler.parse()

    for word, freq in compiler.get_frequencies():
        if freq == 1:
            continue
        print word, freq
    print '-' * 80

    compiler.run('calc')
