from collections import defaultdict
from copy import copy
from ctypes import Union
from io import TextIOWrapper
from typing import Any, Dict, List, Optional, Set, Tuple


# just a wrapper class for a list of strings
# for a production rule 'A -> a A', self.items should be ['a', 'A']
# lambda is stored as an empty string
class Rule:
    def __init__(self, items: List[str]):
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

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.items == other.items


class CFG:
    # pass in path to grammar definition file
    def __init__(self, grammar_file: str):
        """
        for this grammar:
        S -> A $
        A -> a | lambda

        rules would be:
        {
            S: [Rule(['A', '$'])]
            A: [Rule(['a']), Rule([''])
        }
        where the list inside Rule() is that Rule's items
        """
        self.rules: Dict[str, List[Rule]] = defaultdict(list)
        self.alphabet: Set[str] = set()
        self.alphabet_dollar: Set[str] = set()
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

        self.alphabet_dollar = self.alphabet.union(['$'])

    # returns a list of the non-terminals
    def get_non_terminals(self):
        return set(self.rules.keys())

    # returns a list of the terminals and non-terminals (and $)
    def get_grammar_symbols(self):
        return self.alphabet_dollar.union(self.rules.keys())

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
    def derives_to_lambda(self, non_terminal: str, checked=None):
        if non_terminal == '':
            return True
        if non_terminal in self.alphabet:
            return False
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

    def first_set(self, seq: List[str], T: Set[str] = set()) -> Tuple[str, Set[str]]:
        first, *rest = seq
        if first == '':
            return set(), T
        T = copy(T)

        if first in self.alphabet_dollar:
            return {first}, T

        result_set = set()

        if first not in T:
            T.add(first)
            for rule in self.rules[first]:
                sub_result, _ = self.first_set(rule.items, T)
                result_set.update(sub_result)

        if self.derives_to_lambda(first) and len(rest) > 0:
            sub_result, _ = self.first_set(rest, T)
            result_set.update(sub_result)

        return result_set, T

    def follow_set(self, non_terminal: str, T: Set[str] = set()) -> Tuple[Set[str], Set[str]]:
        T = copy(T)

        if non_terminal in T:
            return set(), T

        T.add(non_terminal)
        result_set = set()

        for rule_name in self.rules:
            for rule in self.rules[rule_name]:
                if non_terminal not in rule.items:
                    continue

                for i in range(1, len(rule.items) + 1):
                    if rule.items[i - 1] != non_terminal:
                        continue

                    suffix = rule.items[i:]

                    if i < len(rule.items):
                        sub_result, _ = self.first_set(suffix, set())
                        result_set.update(sub_result)

                    if i == len(rule.items) or (
                            len(self.alphabet_dollar.intersection(suffix)) == 0 and
                            all(self.derives_to_lambda(c) for c in suffix)
                    ):
                        sub_result, _ = self.follow_set(rule_name, T)
                        result_set.update(sub_result)

        return result_set, T

    def predict_set(self, non_terminal: str, rule: Rule) -> set[str]:
        derives_to_lambda = True
        for element in rule.items:
            if not self.derives_to_lambda(element):
                derives_to_lambda = False
                break

        output = self.first_set(rule.items)[0]
        if derives_to_lambda:
            output = output.union(self.follow_set(non_terminal)[0])
        return output

    def check_ll1(self):
        for non_terminal, rules in self.rules.items():
            collective_predict_set = set()
            for rule in rules:
                current_predict_set = self.predict_set(non_terminal, rule)
                current_collective_size = len(collective_predict_set)
                collective_predict_set = collective_predict_set.union(current_predict_set)
                if len(collective_predict_set) != current_collective_size + len(current_predict_set):
                    return False
        return True

    def generate_ll1_table(self) -> Optional[Dict[str, Dict[str, Rule]]]:
        """
        ll1_table is a dictionary of non-terminals to dictionaries from letters to rules
        it might look something like the following:
        {
            NonTerminal1: {a: Rule1, b: Rule2, ...},
            NonTerminal2: {a: Rule3, b: Rule4, ...},
            ...
        }
        note that each "rule" is just the RHS of a production rule,
        so each production rule is uniquely identified by the non-terminal and the "rule"
        """
        ll1_table: Dict[str, Dict[str, Rule]] = defaultdict(lambda: {})

        if not self.check_ll1():
            print('not a valid ll1 grammar')
            return None
        
        for non_terminal, rules in self.rules.items():
            for rule in rules:
                prediction = self.predict_set(non_terminal, rule)
                for symbol in prediction:
                    ll1_table[non_terminal][symbol] = rule
        
        return ll1_table

class Token:
    def __init__(self, type: str, value: str = None):
        self.type = type
        self.value = value
    
    def __repr__(self) -> str:
        s = self.type
        if self.value != None: s+=f"({self.value})"
        return s

class Node:
    def __init__(self, type: str):
        self.type = type
        self.children = [] # List[Union[Node,Leaf]]
    
    def print(self, tabs=0) -> str:
        print('| '*tabs + self.type)
        for child in self.children:
            child.print(tabs + 1)

class Leaf:
    def __init__(self, token: str):
        self.token = token
    
    def print(self, tabs=0) -> str:
        print('| '*tabs + str(self.token))
        

def parse(cfg: CFG, table: Dict[str, Dict[str, Rule]], stream: TextIOWrapper) -> Optional[Node]:
    cur_token: Token = None
    def next_token():
        nonlocal cur_token
        try:
            cur_token = Token(*stream.readline().strip().split())
        except:
            pass
    next_token()
    root = Node('root')
    stack: List[Tuple[str, Union[Node, Leaf]]] = [('S', root)]
    while len(stack):
        symbol, node = stack.pop()

        if isinstance(node, Leaf):
            if node.token != cur_token.type:
                return None
            node.value = cur_token.value
            next_token()
        elif cur_token.type in table[symbol]:
            rule = table[symbol][cur_token.type]
            for part in rule.items[::-1]:
                if part in cfg.alphabet_dollar:
                    new_node = Leaf(part)
                else:
                    new_node = Node(part)
                node.children.insert(0, new_node) # slow, bad.
                stack.append((part, new_node))
        else:
            return None
    
    return root

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
    print()
    print('First set tests:')
    print(cfg.first_set('i'))
    print(cfg.first_set('S'))
    print(cfg.first_set('C'))
    print('Follow set tests:')
    print(cfg.follow_set('S'))
    print(cfg.follow_set('A'))
    print(cfg.follow_set('B'))
    print(cfg.follow_set('C'))
    print(cfg.follow_set('D'))
    print(cfg.follow_set('E'))

    cfg = CFG('test2.cfg')
    print('\nPredict sets')
    for non_terminal, rules in cfg.rules.items():
        for rule in rules:
            print(non_terminal, 'rule:', rule, cfg.predict_set(non_terminal, rule))

    print('\nBuilding table:')
    is_ll1 = cfg.check_ll1()
    print('Is LL(1):', is_ll1)
    if not is_ll1: exit()
    ll1_table = cfg.generate_ll1_table()
    for non_terminal in ll1_table:
        print(f"{non_terminal}: {str(ll1_table[non_terminal])}")
    
    print('\nParse tree')
    tree = parse(cfg, ll1_table, open('tokenstream.txt','r'))
    tree.print()
    

