"""Minimal S-expression reader/writer for KiCad files (lists, quoted strings, bare atoms)."""


class Q(str):
    """A string that was (and must stay) double-quoted."""


def parse(text):
    pos, n, stack, cur = 0, len(text), [], []
    while pos < n:
        c = text[pos]
        if c == "(":
            stack.append(cur); cur = []; pos += 1
        elif c == ")":
            done = cur; cur = stack.pop(); cur.append(done); pos += 1
        elif c == '"':
            j, out = pos + 1, []
            while text[j] != '"':
                if text[j] == "\\":
                    out.append(text[j:j + 2]); j += 2
                else:
                    out.append(text[j]); j += 1
            cur.append(Q("".join(out))); pos = j + 1
        elif c.isspace():
            pos += 1
        else:
            j = pos
            while j < n and not text[j].isspace() and text[j] not in "()":
                j += 1
            cur.append(text[pos:j]); pos = j
    assert not stack, "unbalanced parentheses"
    return cur[0]


def dump(node, indent=0):
    if isinstance(node, Q):
        return f'"{node}"'
    if isinstance(node, str):
        return node
    flat = "(" + " ".join(dump(c) for c in node) + ")"
    if len(flat) <= 110 or not any(isinstance(c, list) for c in node):
        return flat
    pad = "\n" + "  " * (indent + 1)
    head = [dump(c) for c in node if not isinstance(c, list)]
    return "(" + " ".join(head) + "".join(pad + dump(c, indent + 1) for c in node if isinstance(c, list)) + ")"


def find(node, tag):
    return [c for c in node if isinstance(c, list) and c and c[0] == tag]
