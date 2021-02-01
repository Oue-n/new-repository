testa = "BECAUSE (AND (COMINGOUT Agent[05] VILLAGER) (DAY 1 (Agent[04] DIVINED Agent[05] WEREWOLF))) (XOR (ESTIMATE Agent[04] WEREWOLF) (ESTIMATE Agent[04] POSSESSED))"
test = "AND (VOTE Agent[04]) (REQUEST ANY (VOTE Agent[04]))"
test = "((VOTE Agent[04]))"
test = "VOTE Agent[01]"
test = "DAY 1 (DIVINED Agent[04] WEREWOLF)"

import re


def parenthetic_contents(string):
    """Generate parenthesized contents in string as pairs (level, contents)."""
    stack = []
    for i, c in enumerate(string):
        if c == '(':
            stack.append(i)
        elif c == ')' and stack:
            start = stack.pop()
            yield (len(stack), string[start + 1:i])


def parse_text(test):
    test = "("+test+")"
    a = list(parenthetic_contents(test))
    clist = []
    #print(a)
    for i, content in a:
        b = re.search('\(([^)]+)', content)
        if b == None:
            if content.startswith("("):
                continue
            clist.append(content)
        else:
            if b.group().startswith("("):
                continue
            clist.append(b.group())
        # print(b)
    clist = list(map(lambda i: i, clist))
    return clist
