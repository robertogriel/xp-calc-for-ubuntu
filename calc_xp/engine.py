"""Independent calculator engine. No evaluation of Python or shell expressions."""
from decimal import Decimal, localcontext, InvalidOperation, DivisionByZero, Overflow
import math
import re


class Calculator:
    PRECISION = 32
    PRIORITY = {'or': 1, 'xor': 2, 'and': 3, 'lsh': 4, 'rsh': 4, '+': 5, '-': 5,
                '*': 6, '/': 6, 'mod': 6, 'pow': 7, 'root': 7}

    def __init__(self):
        self.mode = 'standard'
        self.base = 10
        self.bits = 32
        self.angle = 'deg'
        self.memory = Decimal(0)
        self.statistics = []
        self.inverse = False
        self.hyperbolic = False
        self.scientific_format = False
        self.clear()

    def clear(self):
        self.entry = '0'
        self.fresh = True
        self.values = []
        self.operators = []
        self.repeat = None
        self.error = None
        self.awaiting = False

    def clear_entry(self):
        self.entry = '0'
        self.fresh = False
        self.error = None

    def set_mode(self, mode):
        self.mode = mode
        self.base = 10
        self.clear()

    def number(self):
        if self.error:
            raise ValueError(self.error)
        if self.base != 10:
            return Decimal(int(self.entry, self.base))
        text = self.entry
        if text.endswith(('e', 'e-', 'e+')):
            text += '0'
        return Decimal(text)

    def put(self, value):
        value = Decimal(value)
        if not value.is_finite() or (value and abs(value.adjusted()) > 9999):
            raise ValueError('Resultado fora do intervalo')
        if self.base != 10:
            number = int(value) & ((1 << self.bits) - 1)
            self.entry = {2: lambda n: format(n, 'b'), 8: lambda n: format(n, 'o'),
                          16: lambda n: format(n, 'X')}[self.base](number)
        else:
            with localcontext() as ctx:
                ctx.prec = self.PRECISION
                value = +value
            self.entry = str(value) if value else '0'
        self.fresh = True

    def digit(self, key):
        if self.error:
            self.clear()
        if self.fresh and not self.operators:
            self.repeat = None
        if key == '.':
            if self.base != 10:
                return
            if self.fresh:
                self.entry = '0'
            if '.' in self.entry or 'e' in self.entry.lower():
                return
            self.entry += '.'
        else:
            if int(key, 16) >= self.base:
                return
            if self.fresh:
                self.entry = key
            elif self.entry in ('0', '-0'):
                self.entry = ('-' if self.entry.startswith('-') else '') + key
            elif len(self.entry.replace('-', '').replace('.', '')) < self.PRECISION:
                self.entry += key
        self.fresh = False
        self.awaiting = False

    def sign(self):
        if 'e' in self.entry.lower() and not self.fresh:
            mantissa, exponent = self.entry.lower().split('e')
            self.entry = mantissa + 'e' + (exponent[1:] if exponent.startswith('-') else '-' + exponent.lstrip('+'))
        elif self.base != 10:
            self.put(-self.number())
        elif self.entry != '0':
            self.entry = self.entry[1:] if self.entry.startswith('-') else '-' + self.entry

    def backspace(self):
        if self.error:
            self.clear()
        elif not self.fresh:
            self.entry = self.entry[:-1]
            if self.entry in ('', '-'):
                self.entry = '0'

    def priority(self, op):
        return self.PRIORITY[op] if self.mode == 'scientific' else 1

    def calculate(self, left, op, right):
        with localcontext() as ctx:
            ctx.prec = self.PRECISION
            if op == '+': return left + right
            if op == '-': return left - right
            if op == '*': return left * right
            if op == '/': return left / right
            if op == 'mod': return left % right
            if op == 'root':
                if left < 0 and right == int(right) and int(right) % 2:
                    return -ctx.power(-left, 1 / right)
                return ctx.power(left, 1 / right)
            if op == 'pow':
                if abs(right) > 10000: raise ValueError('Expoente fora do intervalo')
                return ctx.power(left, right)
            a, b = int(left), int(right)
            mask = (1 << self.bits) - 1
            if op == 'and': return Decimal((a & b) & mask)
            if op == 'or': return Decimal((a | b) & mask)
            if op == 'xor': return Decimal((a ^ b) & mask)
            if op in ('lsh', 'rsh'):
                if not 0 <= b < self.bits: raise ValueError('Deslocamento fora do intervalo')
                return Decimal(((a << b) if op == 'lsh' else ((a & mask) >> b)) & mask)
        raise ValueError('Operação desconhecida')

    def reduce(self):
        op = self.operators.pop()
        right, left = self.values.pop(), self.values.pop()
        result = self.calculate(left, op, right)
        self.values.append(result)
        self.repeat = (op, right)
        return result

    def binary(self, op):
        if self.inverse:
            op = {'pow': 'root', 'lsh': 'rsh'}.get(op, op)
        if self.awaiting and self.operators and self.operators[-1] != '(':
            self.operators[-1] = op
            return
        self.values.append(self.number())
        while self.operators and self.operators[-1] != '(' and self.priority(self.operators[-1]) >= self.priority(op):
            self.put(self.reduce())
        self.operators.append(op)
        self.fresh = True
        self.awaiting = True

    def equals(self):
        if self.operators:
            self.values.append(self.number())
            while self.operators:
                if self.operators[-1] == '(':
                    self.operators.pop()
                else:
                    self.reduce()
            result = self.values.pop()
            self.values.clear()
            self.put(result)
        elif self.repeat:
            op, right = self.repeat
            self.put(self.calculate(self.number(), op, right))
        self.awaiting = False

    def parenthesis(self, closing=False):
        if not closing:
            if not self.fresh:
                self.binary('*')
            self.operators.append('(')
            self.entry = '0'
            self.fresh = True
            self.awaiting = True
        elif '(' in self.operators:
            self.values.append(self.number())
            while self.operators[-1] != '(':
                self.reduce()
            self.operators.pop()
            self.put(self.values.pop())
            # The displayed result becomes the next operand, including in outer parentheses.
            self.fresh = False
            self.awaiting = False

    def percent(self):
        with localcontext() as ctx:
            ctx.prec = self.PRECISION
            value = self.number() / 100
            if self.values:
                value *= self.values[-1]
            self.put(value)
            self.awaiting = False

    def change_base(self, base):
        value = self.number()
        self.base = base
        self.values.clear()
        self.operators.clear()
        self.repeat = None
        self.put(value)

    def unary(self, op):
        x = self.number()
        with localcontext() as ctx:
            ctx.prec = self.PRECISION
            if op == 'sqrt': y = x.sqrt()
            elif op == 'reciprocal': y = 1 / x
            elif op == 'square': y = x.sqrt() if self.inverse else x * x
            elif op == 'cube': y = ctx.power(abs(x), Decimal(1) / 3) * (-1 if x < 0 else 1) if self.inverse else x ** 3
            elif op == 'ln': y = x.exp() if self.inverse else x.ln()
            elif op == 'log': y = ctx.power(10, x) if self.inverse else x.log10()
            elif op == 'factorial':
                if x != int(x) or not 0 <= x <= 1000:
                    raise ValueError('Fatorial requer inteiro entre 0 e 1000')
                y = Decimal(math.factorial(int(x)))
            elif op == 'int': y = x - int(x) if self.inverse else Decimal(int(x))
            elif op == 'not': y = Decimal((~int(x)) & ((1 << self.bits) - 1))
            elif op == 'pi': y = Decimal('3.1415926535897932384626433832795')
            elif op in ('sin', 'cos', 'tan'):
                func = ('a' if self.inverse else '') + op + ('h' if self.hyperbolic else '')
                v = float(x)
                if not self.inverse and not self.hyperbolic:
                    v *= {'deg': math.pi / 180, 'rad': 1, 'grad': math.pi / 200}[self.angle]
                v = getattr(math, func)(v)
                if self.inverse and not self.hyperbolic:
                    v /= {'deg': math.pi / 180, 'rad': 1, 'grad': math.pi / 200}[self.angle]
                y = Decimal(format(v, '.15g'))
            elif op == 'dms':
                a = abs(x)
                if self.inverse:
                    deg = int(a); minutes = int((a - deg) * 100)
                    seconds = (a * 100 - int(a * 100)) * 100
                    y = Decimal(deg) + Decimal(minutes) / 60 + seconds / 3600
                else:
                    deg = int(a); minutes = int((a - deg) * 60)
                    seconds = ((a - deg) * 60 - minutes) * 60
                    y = Decimal(deg) + Decimal(minutes) / 100 + seconds / 10000
                if x < 0: y = -y
            elif op in ('average', 'sum', 'stddev'):
                if not self.statistics: raise ValueError('Nenhum dado estatístico')
                data = self.statistics
                total = sum(data, Decimal(0))
                if op == 'sum': y = sum((v * v for v in data), Decimal(0)) if self.inverse else total
                elif op == 'average': y = total / len(data)
                else:
                    count = len(data) if self.inverse else len(data) - 1
                    if count < 1: raise ValueError('São necessários pelo menos dois dados')
                    mean = total / len(data)
                    y = (sum(((v - mean) ** 2 for v in data), Decimal(0)) / count).sqrt()
            else: raise ValueError('Função desconhecida')
            self.put(y)
            self.awaiting = False

    def paste(self, text):
        text = text.strip().replace('\u2212', '-')
        if len(text) > 256:
            raise ValueError('Número muito longo')
        if self.base == 10:
            text = text.replace(',', '.')
            if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?', text):
                raise ValueError('Cole apenas um número')
            value = Decimal(text)
        else:
            value = Decimal(int(text, self.base))
        self.error = None
        self.put(value)
        self.fresh = False

    def press(self, key):
        try:
            if key in ('C', 'clear'): self.clear()
            elif key == 'CE': self.clear_entry()
            elif key.startswith('digit:'): self.digit(key[6:])
            elif self.error and key not in '0123456789.': return
            elif len(key) == 1 and key in '0123456789ABCDEF.': self.digit(key)
            elif key in self.PRIORITY: self.binary(key)
            elif key == '=': self.equals()
            elif key == '+/-': self.sign()
            elif key == 'Backspace': self.backspace()
            elif key == '%': self.percent()
            elif key == '(': self.parenthesis()
            elif key == ')': self.parenthesis(True)
            elif key == 'MC': self.memory = Decimal(0)
            elif key == 'MR': self.put(self.memory); self.fresh = False; self.awaiting = False
            elif key == 'MS': self.memory = self.number()
            elif key == 'M+':
                with localcontext() as ctx:
                    ctx.prec = self.PRECISION
                    self.memory += self.number()
            elif key == 'Exp':
                if self.base == 10 and 'e' not in self.entry.lower():
                    self.entry = str(self.number()) + 'e'; self.fresh = False
            elif key == 'F-E': self.scientific_format = not self.scientific_format
            elif key == 'Dat': self.statistics.append(self.number())
            else: self.unary(key)
        except (DivisionByZero, ZeroDivisionError): self.error = 'Não é possível dividir por zero.'
        except (InvalidOperation, ValueError, Overflow, OverflowError) as exc:
            self.error = str(exc) if isinstance(exc, ValueError) else 'Entrada inválida para a função.'

    def display(self, grouping=False, decimal_separator=','):
        if self.error: return self.error
        if self.base != 10: return self.entry
        if not self.fresh:
            text = self.entry.replace('.', decimal_separator)
            return text + decimal_separator if '.' not in self.entry and 'e' not in self.entry.lower() else text
        x = self.number()
        if self.scientific_format or (x and (x.adjusted() >= 32 or x.adjusted() <= -10)):
            text = format(x, '.15E')
            mantissa, exponent = text.split('E')
            return mantissa.rstrip('0').rstrip('.').replace('.', decimal_separator) + 'e' + exponent
        text = format(x, 'f')
        if '.' in text: text = text.rstrip('0').rstrip('.')
        whole, _, fraction = text.partition('.')
        if grouping:
            separator = '.' if decimal_separator == ',' else ','
            whole = format(int(whole), ',').replace(',', separator)
        return whole + decimal_separator + fraction
