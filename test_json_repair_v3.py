import json
import re

def repair_json(s):
    s = s.strip()
    stack = []
    in_string = False
    escaped = False
    for char in s:
        if char == '"' and not escaped: in_string = not in_string
        if in_string:
            if char == '\\': escaped = not escaped
            else: escaped = False
            continue
        if char == '{': stack.append('}')
        elif char == '[': stack.append(']')
        elif char == '}':
            if stack and stack[-1] == '}': stack.pop()
        elif char == ']':
            if stack and stack[-1] == ']': stack.pop()
    if in_string: s += '"'
    if stack:
        s = s.rstrip()
        while s and s[-1] not in '"0123456789truefalsenull}]':
            s = s[:-1].rstrip()
        if s.endswith(','): s = s[:-1].rstrip()
        s += "".join(reversed(stack))
    return s

# Test cases
# 1. Truncated mid-string
t1 = '{"title": "The story of my'
r1 = repair_json(t1)
assert json.loads(r1) == {"title": "The story of my"}

# 2. Truncated mid-key
t2 = '{"scenes": [{"id": 1, "dur'
r2 = repair_json(t2)
assert json.loads(r2) == {"scenes": [{"id": 1}]}

# 3. Truncated with trailing comma
t3 = '{"id": 1, "meta": {"a": 1}, '
r3 = repair_json(t3)
assert json.loads(r3) == {"id": 1, "meta": {"a": 1}}

print("✅ Refined JSON Repair tests passed!")
