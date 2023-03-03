from collections import defaultdict


# just a wrapper class for a list of strings
# for a production rule 'A -> a A', self.items should be ['a', 'A']
# lambda is stored as an empty string
class Rule:
    def __init__(self, items):
        self.items = items

    # if items is ['a', 'A'], this returns 'a A'
    # [''] returns 'lambda'
    def __str__(self):
        output = ''
        for item in self.items:
            if item == '':
                item = 'lambda'
            output += item + ' '
        return output[:-1]


class CFG:
    # pass in path to grammar definition file
    def __init__(self, grammar_file):
        """
        for this grammar:
        S -> A $
        A -> a | lambda

        rules would be:
        {
            S: [Rule(['A', '$']]
            A: [Rule(['a']), Rule([''])
        }
        where the list inside Rule() is that Rule's items
        """
        self.rules = defaultdict(lambda: [])
        self.alphabet = set()
        with open(grammar_file, 'r') as grammar:
            lines = [line.strip() for line in grammar.read().split('\n') if line.strip() != '']
            i = 0
            while i < len(lines):
                line = lines[i]
                non_terminal, rules = line.split(' -> ')
                rules = rules.split(' | ')
                while i < len(lines) - 1 and lines[i + 1][0] == '|':
                    i += 1
                    rules += lines[i][2:].split(' | ')
                for rule in rules:
                    if '$' in rule:
                        self.start_symbol = non_terminal
                    elif rule == 'lambda':
                        rule = ''
                    rhs = rule.split(' ')
                    self.alphabet.update(rhs)
                    self.rules[non_terminal].append(Rule(rhs))
                i += 1

        for non_terminal in self.rules.keys():
            if non_terminal in self.alphabet:
                self.alphabet.remove(non_terminal)
        if '' in self.alphabet:
            self.alphabet.remove('')
        if '$' in self.alphabet:
            self.alphabet.remove('$')

    # returns a list of the non-terminals
    def get_non_terminals(self):
        return list(self.rules.keys())

    # returns a list of the terminals and non-terminals (and $)
    def get_grammar_symbols(self):
        symbols = self.alphabet.union(self.rules.keys())
        symbols.add('$')
        return list(symbols)

    # if self.rules is { S -> [Rule(['a', '$']), Rule([''])] }
    # this returns
    # (1)    S -> a $
    # (2)    S -> lambda
    def get_rules_string(self):
        output = ''
        i = 1
        for non_terminal in self.get_non_terminals():
            for rule in self.rules[non_terminal]:
                output += f"({i})    {non_terminal} -> {str(rule)}\n"
                i += 1

        return output

    # pass in the name of a non_terminal
    # don't pass anything for checked
    def derives_to_lambda(self, non_terminal, checked=None):
        if checked is None:
            checked = []
        for rule in self.rules[non_terminal]:
            if rule in checked:
                continue
            if rule.items == ['']:
                return True
            if len(self.alphabet.intersection(rule.items)) > 0:
                continue
            all_derive_lambda = True
            for symbol in rule.items:
                checked.append(rule)
                all_derive_lambda = self.derives_to_lambda(symbol, checked)
                checked.pop()
                if not all_derive_lambda:
                    break
            if all_derive_lambda:
                return True

        return False


# print things in the example format from lga-cfg-code
if __name__ == '__main__':
    cfg = CFG('test.cfg')
    print('Grammar Non-Terminals')
    print(str(cfg.get_non_terminals()).replace('\'', '')[1:-1])
    print('Grammar Symbols')
    print(str(cfg.get_grammar_symbols()).replace('\'', '')[1:-1])
    print()
    print(cfg.get_rules_string())
    print()
    print('Grammar Start Symbol or Goal:', cfg.start_symbol)
    print(cfg.derives_to_lambda('C'))
    print(cfg.derives_to_lambda('D'))
