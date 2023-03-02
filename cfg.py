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
                    self.rules[non_terminal].append(Rule(rule.split(' ')))
                i += 1

    # returns a list of the non-terminals
    def get_non_terminals(self):
        return list(self.rules.keys())

    # returns a list of the terminals and non-terminals (and $)
    def get_grammar_symbols(self):
        symbols = set(self.get_non_terminals())
        for rule_set in self.rules.values():
            for rule in rule_set:
                symbols.update(rule.items)
        if '' in symbols:
            symbols.remove('')

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
