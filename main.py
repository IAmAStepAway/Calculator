from collections import deque


class Token:
    def __init__(self, name='', attr='', prior=0):
        self._name = name
        self._attr = attr
        self.prior = prior

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def attr(self):
        return self._attr

    @attr.setter
    def attr(self, value):
        self._attr = value

    @property
    def prior(self):
        return self._prior

    @prior.setter
    def prior(self, value):
        self._prior = value

    def __str__(self):
        return f'<{self.name}, "{self.attr}">'

    def __repr__(self):
        return f'Token("{self.name}", "{self.attr}", "{self._prior}")'


class Tokenizer:
    def __init__(self, expr=''):
        self._begin_pos = 0
        self._end_pos = 0
        self._mid_pos = 0
        self._state = 0
        self._expr = expr + '\n'
        self._STATE_TABLE = [
            [+1, +1, -2],
            [+2, -1, +2],
            [-3, -1, -2],
            [-4, -1, -2],
            [-5, -1, -2],
            [-6, -1, -2],
            [-7, -1, -2],
            [-8, -1, -2],
        ]
        self._TOKEN_PARAMS = {
            -1: ['digit', 1],
            -2: ['sp', 0],
            -3: ['+', 2],
            -4: ['-', 2],
            -5: ['*', 3],
            -6: ['/', 3],
            -7: ['(', 4],
            -8: [')', 4],
        }

    @property
    def expr(self):
        return self._expr

    @expr.setter
    def expr(self, value):
        self._expr = value + '\n'

    @staticmethod
    def _get_sym_num(symbol):
        if symbol.isdigit():
            return 1
        elif symbol.isspace():
            return 2
        elif symbol == '+':
            return 3
        elif symbol == '-':
            return 4
        elif symbol == '*':
            return 5
        elif symbol == '/':
            return 6
        elif symbol == '(':
            return 7
        elif symbol == ')':
            return 8

    def _get_next_state(self, symbol):
        sym_num = self._get_sym_num(symbol)
        return self._STATE_TABLE[sym_num-1][self._state]

    def _get_lexem(self):
        if self._end_pos >= len(self._expr) - 1:
            return None

        self._state = 0
        self._mid_pos = self._begin_pos = self._end_pos

        while self._state >= 0:
            self._state = self._get_next_state(self._expr[self._mid_pos])
            self._mid_pos += 1

        self._end_pos = self._mid_pos - self._get_ret_poss_count()

        return self._expr[self._begin_pos: self._end_pos]

    def _get_ret_poss_count(self):
        return 1 if self._state in (-1, -2) else 0

    def get_token(self):
        lexem = self._get_lexem()
        return Token(self._TOKEN_PARAMS[self._state][0], lexem, self._TOKEN_PARAMS[self._state][1]) if lexem else None


class Calculator:
    def __init__(self, expr=''):
        self._expr = expr
        self._tokens = []
        self._queue = deque()
        self._stack = []

    @property
    def expr(self):
        return self._expr

    @expr.setter
    def expr(self, value):
        self._expr = value

    def _transf_expr_to_tokens(self):
        tokenizer = Tokenizer(self._expr)
        self._tokens = []
        token = tokenizer.get_token()
        while token:
            if token.name != 'sp':
                self._tokens.append(token)
            token = tokenizer.get_token()

    def _infix_to_postfix(self):
        tokens_count = len(self._tokens)
        for i in range(tokens_count):
            token = self._tokens[i]

            # 1. Если входящий элемент число, то добавляем его в очередь
            if token.name == 'digit':
                self._queue.append(token)

            # 2. Если входящий элемент оператор(+, -, *, /) то проверяем:
            if token.name in ('+', '-', '*', '/'):
                # Если стек(STACK) пуст или содержит левую скобку в вершине(TOP),
                # то добавляем(PUSH) входящий оператор в стек(STACK).
                if (not len(self._stack)) or self._stack[len(self._stack)-1] == '(':
                    self._stack.append(token)
                # Если входящий оператор имеет более высокий приоритет чем
                # вершина (TOP), поместите (PUSH) его в стек (STACK).
                elif token.prior > self._stack[len(self._stack)-1].prior:
                    self._stack.append(token)
                # Если входящий оператор имеет более низкий или равный приоритет,
                # чем вершине (TOP), выгружаем POP в очередь (QUEUE), пока не увидите
                # оператор с меньшим приоритетом или левую скобку на вершине (TOP),
                # затем добавьте (PUSH) входящий оператор в стек (STACK).
                elif token.prior <= self._stack[len(self._stack)-1].prior:
                    unload = Token(prior=1000)
                    while len(self._stack) and (unload.prior >= token.prior):
                        unload = self._stack.pop()
                        if unload.attr == '(':
                            self._stack.append(unload)
                            break
                        self._queue.append(unload)
                    self._stack.append(token)

                    # while len(self._stack):
                    #     self._queue.append(self._stack.pop())
                    # self._stack.append(token)

            # 3. Если входящий элемент является левой скобкой, поместите (PUSH) его в стек (STACK).
            if token.attr == '(':
                self._stack.append(token)

            # 4. Если входящий элемент является правой скобкой, выгружаем стек (POP) и добавляем
            # его элементы в очередь (QUEUE), пока не увидите левую круглую скобку.
            # Удалите найденную скобку из стека (STACK).
            if token.attr == ')':
                unload = self._stack.pop()
                while unload.attr != '(':
                    if not len(self._stack):
                        print('"(" не найдена.')
                        return
                    self._queue.append(unload)
                    unload = self._stack.pop()

            # 5. В конце выражения выгрузите стек (POP) в очередь (QUEUE)
            if i == tokens_count-1:
                while len(self._stack):
                    unload = self._stack.pop()
                    self._queue.append(unload)

    def _calc_from_postfix(self):
        self._stack = []
        while len(self._queue):
            unload = self._queue.popleft()
            # 1. Если входящий элемент является числом, поместите(PUSH) его в стек (STACK)
            if unload.name == 'digit':
                self._stack.append(unload)
            # 2. Если входящий элемент является оператором (*-/+), необходимо получить (POP)
            # два последних числа из стека (STACK) и выполнить соответствующую операцию.
            # Далее поместите (PUSH) полученный результат в стек (STACK).
            if unload.attr in ('+', '-', '*', '/'):
                term_2 = int(self._stack.pop().attr)
                term_1 = int(self._stack.pop().attr)
                term = 0
                if unload.attr == '+':
                    term = term_1 + term_2
                elif unload.attr == '-':
                    term = term_1 - term_2
                elif unload.attr == '*':
                    term = term_1 * term_2
                elif unload.attr == '/':
                    term = term_1 / term_2
                self._stack.append(Token(name='digit', attr=str(term)))
        # 3. Когда выражение закончится, число на вершине (TOP) стека (STACK) является результатом.
        return self._stack.pop().attr

    def calc(self, expr=None):
        if expr:
            self._expr = expr
        self._transf_expr_to_tokens()
        self._infix_to_postfix()
        return self._calc_from_postfix()


def main():
    expression = '5*6+(2-9)'
    calculator = Calculator(expression)
    print(f'{expression} = {calculator.calc()}')

    expression = '6 * (52 + 3) * 4'
    print(f'{expression} = {calculator.calc(expression)}')

    expression = '6 * 4'
    print(f'{expression} = {calculator.calc(expression)}')


if __name__ == '__main__':
    main()
