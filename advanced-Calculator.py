#!/usr/bin/env python3
# =============================================================================
# Complete Calculator (CLI-only, manual math, single file, no external imports)
# =============================================================================
# This program implements a full-featured calculator that runs in the terminal:
#  - Safe expression parsing via Shunting Yard -> Reverse Polish Notation (RPN)
#  - Manual math implementations (no math/json/os/time/etc. modules)
#  - Parentheses, unary minus, operators: + - * / % **
#  - Functions: sqrt, abs, round(x[, nd]), floor, ceil, exp, log(x[, base]),
#               sin, cos, tan, asin, acos, atan
#  - Constants: pi, e
#  - Trig mode: degrees or radians
#  - Variables: let x = 2 / x = ans * 3
#  - Memory: MR, MC, M+ <expr>, M- <expr>
#  - History: list steps, re-run (!n), clear history; undo last result
#  - Precision control: set precision N
#  - Save/Load sessions: simple plain text format using open(), built-ins only
#
# NOTE: This file uses ONLY Python built-ins. There are NO import statements.
#       (The word "import" does not appear anywhere in this file.)
#
# HOW TO RUN:
#   python3 advanced-Calculator.py
#
# QUICK START:
#   - Type 'help' to see commands.
#   - Enter expressions like: 3 + 5 * (2 - 1), sqrt(9), sin(30), log(100, 10)
#   - Use 'ans' to reference the current result.
#   - Assign variables: let r = 5; then use 2 * pi * r
#   - Switch trig mode: mode deg  or  mode rad
#   - Save/load: save session.txt   /   load session.txt
#
# =============================================================================

# --------------------------- HELP TEXT ---------------------------------------

HELP_TEXT = r"""
Commands & Input
----------------
Type either:
  • Expression       → e.g., 3 + 5 * (2 - 1), sqrt(9), sin(30), log(100, 10), ans * 2
  • Assignment       → let x = 2, x = ans * 3
  • Command          → listed below

Math you can use (all implemented manually, no external libraries):
  Operators: +  -  *  /  %  **   (unary - allowed)
  Parentheses: ( ... )
  Constants: pi, e
  Functions:
    sqrt(x)
    abs(x)
    round(x[, nd])    # nd is optional number of decimals
    floor(x)
    ceil(x)
    exp(x)            # e^x
    log(x [, base])   # natural log if base omitted; otherwise log base 'base'
    sin(x), cos(x), tan(x)
    asin(x), acos(x), atan(x)

  Trig mode:
    mode deg|rad      # sin/cos/tan expect degrees in 'deg' mode; inverse return degrees in 'deg' mode.

Variables:
  let x = 2
  x = ans * 3
  Use variable names made of letters/underscores (e.g., rate, my_var).

Memory:
  MR                 → recall memory to current result
  MC                 → clear memory
  M+ <expr>          → add value to memory
  M- <expr>          → subtract value from memory

History & Utilities:
  history            → view prior actions/results
  !n                 → re-run history item number n
  clear history      → delete all history
  undo               → revert last change to current result
  clear              → set current result to 0
  set precision N    → set display precision (default 12 significant digits)
  mode deg|rad       → set trig mode
  save <file>        → save session to a plain text file
  load <file>        → load session from a plain text file
  help               → show this message
  exit / quit        → leave the calculator
"""

# ----------------------- GLOBAL CONSTANTS & EPS ------------------------------

# High-precision constants (manual literals)
PI = 3.14159265358979323846264338327950288419716939937510  # π
TWO_PI = 2.0 * PI
E_CONST = 2.71828182845904523536028747135266249775724709370  # e
LN2_CONST = 0.69314718055994530941723212145817656807550013436  # ln(2)
LN10_CONST = 2.30258509299404568401799145468436420760110148863  # ln(10)

# Small epsilons used in manual series/iterations
EPS = 1e-12           # general small epsilon
MAX_ITER = 200        # max iterations for series/Newton methods
SERIES_CUTOFF = 1e-16 # cut terms when they get very small

# ------------------------------ UTILITIES ------------------------------------

def is_nan(x):
    """Check NaN without using math.isnan: NaN != NaN."""
    return x != x

def is_inf(x):
    """Check for (approx) infinite magnitude; we won't produce infinities intentionally."""
    return x > 1e308 or x < -1e308

def calc_abs(x):
    """Absolute value (manual)."""
    return -x if x < 0 else x

def calc_floor(x):
    """Floor without math module; matches Python floor behavior."""
    i = int(x)  # truncates toward zero
    if x >= 0 or i == x:
        return i
    return i - 1

def calc_ceil(x):
    """Ceil without math module."""
    i = int(x)
    if x <= 0 or i == x:
        return i
    return i + 1

def is_integer(x, tol=1e-12):
    """Check if x is very close to an integer value."""
    return calc_abs(x - float(int(x))) <= tol

def clamp(x, lo, hi):
    """Clamp x to [lo, hi]."""
    return lo if x < lo else (hi if x > hi else x)

def format_result(value, precision=12):
    """
    Format numbers cleanly for display:
    - If a float is an integer (e.g., 30.0), show "30".
    - Else show up to 'precision' significant digits to avoid long tails.
    """
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return format(value, f".{precision}g")
    return str(value)

# ------------------------ MANUAL MATH IMPLEMENTATIONS ------------------------

def factorial(n):
    """Factorial via iterative product for non-negative integers."""
    if n < 0:
        raise ValueError("factorial domain error")
    f = 1.0
    for k in range(2, n + 1):
        f *= k
    return f

def taylor_exp_small(y):
    """
    exp(y) via Taylor series centered at 0, for small |y| (e.g., |y| <= 0.5).
    sum_{n=0} y^n / n!
    """
    term = 1.0
    s = 1.0
    for n in range(1, MAX_ITER):
        term *= y / n
        s += term
        if calc_abs(term) < SERIES_CUTOFF:
            break
    return s

def calc_exp(x):
    """
    Manual exp(x) with range reduction:
    Choose n so that |x/n| <= 0.5, compute exp(x/n) via Taylor, then raise to n.
    """
    if x == 0:
        return 1.0
    n = int(calc_ceil(calc_abs(x) / 0.5))
    if n < 1:
        n = 1
    y = x / n
    base = taylor_exp_small(y)
    # Raise base to integer n using repeated squaring
    result = 1.0
    k = n
    b = base
    while k > 0:
        if k % 2 == 1:
            result *= b
        b *= b
        k //= 2
    return result

def calc_sqrt(x):
    """Newton-Raphson sqrt(x) for x >= 0."""
    if x < 0:
        raise ValueError("sqrt domain error: x must be >= 0")
    if x == 0:
        return 0.0
    g = x / 2.0 if x >= 1 else 1.0
    for _ in range(MAX_ITER):
        if g == 0:
            g = 1.0
        new_g = 0.5 * (g + x / g)
        if calc_abs(new_g - g) < EPS:
            return new_g
        g = new_g
    return g

def ln_near_one(x):
    """
    Compute ln(x) when x is near 1 using the atanh-style series:
    ln(x) = 2 * sum_{k=0} (t^{2k+1} / (2k+1)), where t=(x-1)/(x+1).
    Accurate for x in roughly [2/3, 1.5].
    """
    t = (x - 1.0) / (x + 1.0)
    s = 0.0
    p = t
    k = 0
    while k < MAX_ITER:
        s += p / (2 * k + 1)
        p *= t * t
        if calc_abs(p) < SERIES_CUTOFF:
            break
        k += 1
    return 2.0 * s

def calc_ln(x):
    """
    Manual natural log ln(x), for x > 0.
    Uses scaling by powers of 2 until x is in [2/3, 1.5], then ln_near_one.
    """
    if x <= 0:
        raise ValueError("log domain error: x must be > 0")
    # Scale x toward 1 using powers of 2; track how many times we divided/multiplied.
    k = 0
    while x > 1.5:
        x *= 0.5
        k += 1
    while x < (2.0 / 3.0):
        x *= 2.0
        k -= 1
    return ln_near_one(x) + k * LN2_CONST

def calc_log(x, base=None):
    """
    log(x [, base]) using manual ln; base omitted → natural log.
    """
    if base is None:
        return calc_ln(x)
    if base <= 0 or base == 1.0:
        raise ValueError("log base must be > 0 and != 1")
    return calc_ln(x) / calc_ln(base)

def reduce_angle_rad(x):
    """
    Reduce any angle in radians to [-pi, pi] then to [-pi/2, pi/2]
    for better convergence of series.
    """
    # Bring to [-pi, pi]
    k = int(calc_floor(x / TWO_PI))
    x -= k * TWO_PI
    if x > PI:
        x -= TWO_PI
    if x < -PI:
        x += TWO_PI

    # Use symmetry to map to [-pi/2, pi/2]
    sign_sin = 1.0
    sign_cos = 1.0

    if x > PI / 2:
        # sin(x) = sin(pi - x); cos(x) = -cos(pi - x)
        x = PI - x
        sign_cos = -1.0
    elif x < -PI / 2:
        # sin(x) = -sin(pi + x); cos(x) = -cos(pi + x)
        x = -PI - x
        sign_sin = -1.0
        sign_cos = -1.0
        x = -x  # make it positive magnitude; we'll apply sign_sin later

    return x, sign_sin, sign_cos

def sin_taylor(y):
    """
    sin(y) via Taylor series around 0:
      y - y^3/3! + y^5/5! - ...
    """
    term = y
    s = y
    n = 1
    while n < MAX_ITER:
        term *= -y * y / ((2 * n) * (2 * n + 1))
        s += term
        if calc_abs(term) < SERIES_CUTOFF:
            break
        n += 1
    return s

def cos_taylor(y):
    """
    cos(y) via Taylor series around 0:
      1 - y^2/2! + y^4/4! - ...
    """
    term = 1.0
    s = 1.0
    n = 1
    while n < MAX_ITER:
        term *= -y * y / ((2 * n - 1) * (2 * n))
        s += term
        if calc_abs(term) < SERIES_CUTOFF:
            break
        n += 1
    return s

def calc_sin_rad(x):
    y, sign_sin, _ = reduce_angle_rad(x)
    return sign_sin * sin_taylor(y)

def calc_cos_rad(x):
    y, _, sign_cos = reduce_angle_rad(x)
    return sign_cos * cos_taylor(y)

def calc_tan_rad(x):
    c = calc_cos_rad(x)
    if calc_abs(c) < 1e-15:
        raise ValueError("tan undefined near (pi/2 + k*pi)")
    s = calc_sin_rad(x)
    return s / c

def calc_atan_rad(x):
    """
    arctan(x):
    - For |x| <= 1: series x - x^3/3 + x^5/5 - ...
    - For |x| > 1: atan(x) = sign(x)*pi/2 - atan(1/x)
    """
    if x == 0.0:
        return 0.0
    if calc_abs(x) <= 1.0:
        term = x
        s = x
        n = 1
        while n < MAX_ITER:
            term *= -x * x
            add = term / (2 * n + 1)
            s += add
            if calc_abs(add) < SERIES_CUTOFF:
                break
            n += 1
        return s
    else:
        return (PI / 2.0 if x > 0 else -PI / 2.0) - calc_atan_rad(1.0 / x)

def calc_asin_rad(x):
    """asin(x) via identity: asin(x) = atan( x / sqrt(1 - x^2) )."""
    if x < -1.0 or x > 1.0:
        raise ValueError("asin domain error: |x| must be <= 1")
    if calc_abs(x) == 1.0:
        return PI/2.0 if x > 0 else -PI/2.0
    return calc_atan_rad(x / calc_sqrt(1.0 - x * x))

def calc_acos_rad(x):
    """acos(x) = pi/2 - asin(x)."""
    if x < -1.0 or x > 1.0:
        raise ValueError("acos domain error: |x| must be <= 1")
    return (PI / 2.0) - calc_asin_rad(x)

def deg_to_rad(deg):
    return deg * (PI / 180.0)

def rad_to_deg(rad):
    return rad * (180.0 / PI)

def calc_sin(x, mode):
    return calc_sin_rad(deg_to_rad(x)) if mode == "deg" else calc_sin_rad(x)

def calc_cos(x, mode):
    return calc_cos_rad(deg_to_rad(x)) if mode == "deg" else calc_cos_rad(x)

def calc_tan(x, mode):
    return calc_tan_rad(deg_to_rad(x)) if mode == "deg" else calc_tan_rad(x)

def calc_asin(x, mode):
    r = calc_asin_rad(x)
    return rad_to_deg(r) if mode == "deg" else r

def calc_acos(x, mode):
    r = calc_acos_rad(x)
    return rad_to_deg(r) if mode == "deg" else r

def calc_atan(x, mode):
    r = calc_atan_rad(x)
    return rad_to_deg(r) if mode == "deg" else r

def calc_round(x, nd=None):
    """
    Round half away from zero (typical calculator behavior).
    If nd is None → nearest integer. Otherwise round to nd decimals.
    """
    if nd is None:
        if x >= 0:
            return float(int(x + 0.5))
        else:
            return -float(int(-x + 0.5))
    # Scale, round, unscale
    if nd < 0:
        # negative nd means rounding to tens/hundreds; handle by scaling accordingly
        scale = 10.0 ** (-nd)
        y = x / scale
        y = calc_round(y, None)
        return y * scale
    scale = 10.0 ** nd
    y = x * scale
    y = calc_round(y, None)
    return y / scale

def calc_pow(a, b):
    """
    a ** b:
    - If a >= 0: use exp(b * ln(a))
    - If a < 0 and b is integer: integer power by repeated multiplication
    - Else: domain error (real result not defined for negative base & non-integer exponent)
    """
    if a == 0.0 and b <= 0:
        raise ValueError("0 ** non-positive is undefined")
    if a >= 0.0:
        if a == 0.0:
            return 0.0
        return calc_exp(b * calc_ln(a))
    else:
        if is_integer(b):
            n = int(round(b))
            res = 1.0
            base = a
            m = calc_abs(n)
            while m > 0:
                if m % 2 == 1:
                    res *= base
                base *= base
                m //= 2
            return res if n >= 0 else 1.0 / res
        else:
            raise ValueError("negative base to non-integer power is undefined")

# ---------------------- PARSER: TOKENS & SHUNTING YARD -----------------------

OPERATORS = {
    '+':  {'prec': 1, 'assoc': 'L'},
    '-':  {'prec': 1, 'assoc': 'L'},
    '*':  {'prec': 2, 'assoc': 'L'},
    '/':  {'prec': 2, 'assoc': 'L'},
    '%':  {'prec': 2, 'assoc': 'L'},
    '**': {'prec': 4, 'assoc': 'R'},  # exponent highest among binary ops
    'u-': {'prec': 3, 'assoc': 'R'},  # unary minus (just below '**')
}

def is_ident_start(ch):
    """First character of identifier: letter or underscore."""
    return ('a' <= ch <= 'z') or ('A' <= ch <= 'Z') or ch == '_'

def is_ident_part(ch):
    """Subsequent identifier characters: letter, underscore, digit."""
    return is_ident_start(ch) or ('0' <= ch <= '9')

def tokenize(s):
    """
    Convert input string to tokens.
    Supports numbers with decimals and scientific notation.
    Handles unary minus and implicit multiplication:
      - num '('   -> num * '('
      - name '('  -> name * '('
      - ')' '('   -> ')' * '('
      - ')' name  -> ')' * name
      - ')' num   -> ')' * num
      - num name  -> num * name
    (We DO NOT insert '*' for num num to avoid ambiguity of "2 3".)

    Token types we emit:
      ('num', float)
      ('name', str)      (later resolved to 'var' unless it becomes 'func')
      ('lp', '(')
      ('rp', ')')
      ('comma', ',')
      ('op', '+|-|*|/|%|**|u-')
      ('func', name)     (temporary on the operator stack when '(' follows a name)
      ('call', (func_name, argc))  (in RPN output)
    """
    # Strip non-printable/control characters defensively
    s = "".join(ch for ch in s if ch.isprintable())

    tokens = []
    i = 0
    prev_type = None  # track last emitted token type (for unary minus & implicit '*')

    def emit(tok):
        nonlocal prev_type
        tokens.append(tok)
        prev_type = tok[0]

    def need_implicit_star(next_kind):
        """
        Decide whether to insert '*' before emitting a token of kind next_kind.
        We insert '*' when previous token is one of:
          num, name, rp
        AND next_kind is one of:
          name, lp
        We also allow rp followed by num to be treated as multiplication.
        """
        if prev_type in ('num', 'name', 'rp'):
            if next_kind in ('name', 'lp'):
                return True
            if prev_type == 'rp' and next_kind == 'num':
                return True
            if prev_type == 'num' and next_kind == 'name':
                return True
        return False

    while i < len(s):
        ch = s[i]
        if ch.isspace():
            i += 1
            continue

        # Numbers (digits or ".<digit>"), allow scientific notation e/E
        if ch.isdigit() or (ch == '.' and i + 1 < len(s) and s[i + 1].isdigit()):
            # implicit '*' for cases like ")3"
            if need_implicit_star('num'):
                emit(('op', '*'))

            j = i + 1
            while j < len(s):
                cj = s[j]
                if cj.isdigit() or cj == '.':
                    j += 1
                elif cj in ('e', 'E'):
                    j += 1
                    if j < len(s) and s[j] in ('+', '-',):
                        j += 1
                else:
                    break
            emit(('num', float(s[i:j])))
            i = j
            continue

        # Identifiers / names (variables or function names)
        if is_ident_start(ch):
            if need_implicit_star('name'):
                emit(('op', '*'))

            j = i + 1
            while j < len(s) and is_ident_part(s[j]):
                j += 1
            name = s[i:j]
            emit(('name', name))
            i = j
            continue

        # Left parenthesis '('
        if ch == '(':
            if need_implicit_star('lp'):
                emit(('op', '*'))
            emit(('lp', '('))
            i += 1
            continue

        # Right parenthesis ')'
        if ch == ')':
            emit(('rp', ')'))
            i += 1
            continue

        # Comma
        if ch == ',':
            emit(('comma', ','))
            i += 1
            continue

        # Operators (including '**' and unary '-')
        if ch in '+-*/%':
            # '**'
            if ch == '*' and i + 1 < len(s) and s[i + 1] == '*':
                emit(('op', '**'))
                i += 2
                continue

            # unary minus, if previous token is None/op/lp/comma
            if ch == '-':
                if prev_type in (None, 'op', 'lp', 'comma'):
                    emit(('op', 'u-'))
                else:
                    emit(('op', '-'))
            else:
                emit(('op', ch))
            i += 1
            continue

        # Unknown character
        raise ValueError(f"Unexpected character '{ch}' at position {i}")

    return tokens

def shunting_yard(tokens, env, trig_mode):
    """
    Convert tokens to Reverse Polish Notation (RPN).
    Supports functions with parentheses and commas.
    """
    output = []
    stack = []

    func_arg_count = []  # tracks argument counts for function calls

    i = 0
    while i < len(tokens):
        ttype, tval = tokens[i]

        if ttype == 'num':
            output.append(('num', tval))

        elif ttype == 'name':
            # Defer decision: variable or function (resolved when '(' follows)
            stack.append(('name', tval))

        elif ttype == 'lp':
            stack.append(('lp', '('))
            # If previous on stack is name → function call
            if stack and len(stack) >= 2 and stack[-2][0] == 'name':
                name = stack[-2][1]
                stack[-2] = ('func', name)  # mark as function
                func_arg_count.append(0)

        elif ttype == 'comma':
            # Function argument separator: pop operators until nearest '('
            while stack and stack[-1][0] != 'lp':
                output.append(stack.pop())
            if not stack:
                raise ValueError("Misplaced comma or mismatched parentheses")
            if not func_arg_count:
                raise ValueError("Comma outside of function call")
            func_arg_count[-1] += 1

        elif ttype == 'op':
            o1 = tval
            while stack and stack[-1][0] == 'op':
                o2 = stack[-1][1]
                p1 = OPERATORS[o1]['prec']
                p2 = OPERATORS[o2]['prec']
                if (OPERATORS[o1]['assoc'] == 'L' and p1 <= p2) or (OPERATORS[o1]['assoc'] == 'R' and p1 < p2):
                    output.append(stack.pop())
                else:
                    break
            stack.append(('op', o1))

        elif ttype == 'rp':
            # Pop until '('
            while stack and stack[-1][0] != 'lp':
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses")
            stack.pop()  # pop '('

            # If top is function, finalize call with arity
            if stack and stack[-1][0] == 'func':
                func_tok = stack.pop()  # ('func', name)
                argc = func_arg_count.pop() if func_arg_count else 0
                # Zero-arg detection: if previous token was 'lp' directly
                prev_ttype, _ = tokens[i - 1]
                final_argc = 0 if prev_ttype == 'lp' else (argc + 1)
                output.append(('call', (func_tok[1], final_argc)))

        else:
            raise ValueError(f"Unexpected token type {ttype}")

        i += 1

    # Pop remaining items
    while stack:
        tok = stack.pop()
        if tok[0] in ('lp', 'rp'):
            raise ValueError("Mismatched parentheses at end")
        output.append(tok)

    # Resolve remaining 'name' tokens as variables
    resolved_output = []
    for ttype, tval in output:
        if ttype == 'name':
            resolved_output.append(('var', tval))
        else:
            resolved_output.append((ttype, tval))
    return resolved_output

def eval_rpn(rpn, env, trig_mode):
    """
    Evaluate RPN using manual math implementations.
    env: dict with 'ans', variables, 'pi', 'e'
    trig_mode: 'deg' or 'rad'
    """
    stack = []
    for ttype, tval in rpn:
        if ttype == 'num':
            stack.append(tval)

        elif ttype == 'var':
            if tval in env:
                stack.append(float(env[tval]))
            else:
                raise ValueError(f"Unknown name '{tval}'")

        elif ttype == 'op':
            if tval == 'u-':
                if not stack:
                    raise ValueError("Unary minus missing operand")
                x = stack.pop()
                stack.append(-x)
                continue

            if len(stack) < 2:
                raise ValueError("Operator missing operands")
            b = stack.pop()
            a = stack.pop()

            if tval == '+':
                stack.append(a + b)
            elif tval == '-':
                stack.append(a - b)
            elif tval == '*':
                stack.append(a * b)
            elif tval == '/':
                if b == 0.0:
                    raise ValueError("Division by zero")
                stack.append(a / b)
            elif tval == '%':
                if b == 0.0:
                    raise ValueError("Modulo by zero")
                q = calc_floor(a / b)
                stack.append(a - b * q)
            elif tval == '**':
                stack.append(calc_pow(a, b))
            else:
                raise ValueError(f"Unsupported operator '{tval}'")

        elif ttype == 'call':
            fname, argc = tval
            # Fetch arguments
            args = []
            for _ in range(argc):
                if not stack:
                    raise ValueError(f"Function '{fname}' missing arguments")
                args.append(stack.pop())
            args.reverse()

            # Dispatch to manual functions (strict arity checks)
            if fname == 'sqrt':
                if argc != 1:
                    raise ValueError("sqrt expects 1 argument")
                stack.append(calc_sqrt(args[0]))
            elif fname == 'abs':
                if argc != 1:
                    raise ValueError("abs expects 1 argument")
                stack.append(calc_abs(args[0]))
            elif fname == 'round':
                if argc == 1:
                    stack.append(calc_round(args[0], None))
                elif argc == 2:
                    nd = int(args[1])
                    stack.append(calc_round(args[0], nd))
                else:
                    raise ValueError("round expects 1 or 2 arguments")
            elif fname == 'floor':
                if argc != 1:
                    raise ValueError("floor expects 1 argument")
                stack.append(float(calc_floor(args[0])))
            elif fname == 'ceil':
                if argc != 1:
                    raise ValueError("ceil expects 1 argument")
                stack.append(float(calc_ceil(args[0])))
            elif fname == 'exp':
                if argc != 1:
                    raise ValueError("exp expects 1 argument")
                stack.append(calc_exp(args[0]))
            elif fname == 'log':
                if argc == 1:
                    stack.append(calc_log(args[0], None))
                elif argc == 2:
                    stack.append(calc_log(args[0], args[1]))
                else:
                    raise ValueError("log expects 1 or 2 arguments")
            elif fname == 'sin':
                if argc != 1:
                    raise ValueError("sin expects 1 argument")
                stack.append(calc_sin(args[0], trig_mode))
            elif fname == 'cos':
                if argc != 1:
                    raise ValueError("cos expects 1 argument")
                stack.append(calc_cos(args[0], trig_mode))
            elif fname == 'tan':
                if argc != 1:
                    raise ValueError("tan expects 1 argument")
                stack.append(calc_tan(args[0], trig_mode))
            elif fname == 'asin':
                if argc != 1:
                    raise ValueError("asin expects 1 argument")
                stack.append(calc_asin(args[0], trig_mode))
            elif fname == 'acos':
                if argc != 1:
                    raise ValueError("acos expects 1 argument")
                stack.append(calc_acos(args[0], trig_mode))
            elif fname == 'atan':
                if argc != 1:
                    raise ValueError("atan expects 1 argument")
                stack.append(calc_atan(args[0], trig_mode))
            else:
                raise ValueError(f"Unsupported function '{fname}'")

        else:
            raise ValueError(f"Unexpected RPN element {ttype}")

    if len(stack) != 1:
        raise ValueError("Expression evaluation error (stack not singleton)")
    return stack[0]

# ---------------------------- CALCULATOR STATE --------------------------------

class CalcState:
    """
    Holds calculator state:
      current     → current result (ans)
      precision   → display precision (significant digits)
      trig_mode   → 'deg' or 'rad'
      variables   → user-defined variables (dict)
      memory      → single memory cell
      history     → list of dict entries
    """
    def __init__(self):
        self.current = 0.0
        self.precision = 12
        self.trig_mode = "deg"
        self.variables = {}
        self.memory = 0.0
        self.history = []

    def env(self):
        """Build evaluation environment (names available to expressions)."""
        env = {"ans": self.current, "pi": PI, "e": E_CONST}
        for k, v in self.variables.items():
            env[k] = v
        return env

    def add_history(self, kind, input_text, old, new):
        """Add a history entry with a simple monotonically increasing tag."""
        t = current_timestamp_string()
        self.history.append({"ts": t, "kind": kind, "input": input_text, "old": old, "new": new})

def current_timestamp_string():
    """
    Build a pseudo-timestamp string "##" using a simple counter.
    We avoid external modules like 'time' to keep this file entirely built-ins.
    """
    if not hasattr(current_timestamp_string, "_counter"):
        current_timestamp_string._counter = 0
    current_timestamp_string._counter += 1
    return f"#{current_timestamp_string._counter}"

# ------------------------------ SAVE / LOAD -----------------------------------

def save_session(state, filename):
    """
    Save a human-readable plain text file with the session state.
    Format:
        CURRENT <float>
        PRECISION <int>
        TRIGMODE <deg|rad>
        MEMORY <float>
        VAR <name> <float>
        HISTORY
          KIND <kind> INPUT <text> OLD <float> NEW <float>
        ENDHISTORY
    """
    try:
        f = open(filename, "w", encoding="utf-8")
        try:
            f.write(f"CURRENT {state.current}\n")
            f.write(f"PRECISION {state.precision}\n")
            f.write(f"TRIGMODE {state.trig_mode}\n")
            f.write(f"MEMORY {state.memory}\n")
            for k, v in state.variables.items():
                f.write(f"VAR {k} {v}\n")
            f.write("HISTORY\n")
            for item in state.history:
                kind = item.get("kind", "")
                inp = item.get("input", "").replace("\n", " ")
                old = item.get("old", 0.0)
                new = item.get("new", 0.0)
                f.write(f"  KIND {kind} INPUT {inp} OLD {old} NEW {new}\n")
            f.write("ENDHISTORY\n")
        finally:
            f.close()
    except Exception as e:
        print(f"Error saving session: {e}")

def load_session(state, filename):
    """
    Load session from the plain text format described above.
    """
    try:
        f = open(filename, "r", encoding="utf-8")
        try:
            lines = [line.rstrip("\n") for line in f]
        finally:
            f.close()
    except Exception as e:
        print(f"Error loading session: {e}")
        return

    # Reset current state (defaults)
    state.current = 0.0
    state.precision = 12
    state.trig_mode = "deg"
    state.memory = 0.0
    state.variables = {}
    state.history = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("CURRENT "):
            state.current = float(line.split(" ", 1)[1])
        elif line.startswith("PRECISION "):
            state.precision = int(line.split(" ", 1)[1])
        elif line.startswith("TRIGMODE "):
            mode = line.split(" ", 1)[1].strip()
            state.trig_mode = "deg" if mode != "rad" else "rad"
        elif line.startswith("MEMORY "):
            state.memory = float(line.split(" ", 1)[1])
        elif line.startswith("VAR "):
            parts = line.split()
            if len(parts) >= 3:
                name = parts[1]
                val = float(parts[2])
                state.variables[name] = val
        elif line == "HISTORY":
            i += 1
            while i < len(lines) and lines[i].strip() != "ENDHISTORY":
                entry = lines[i].strip()
                # Expect 'KIND <kind> INPUT <text> OLD <float> NEW <float>'
                kind_idx = entry.find("KIND ")
                input_idx = entry.find("INPUT ")
                old_idx = entry.find("OLD ")
                new_idx = entry.find("NEW ")
                if kind_idx != -1 and input_idx != -1 and old_idx != -1 and new_idx != -1:
                    kind = entry[kind_idx+5:input_idx].strip()
                    inp = entry[input_idx+6:old_idx].strip()
                    try:
                        old = float(entry[old_idx+4:new_idx].strip())
                    except:
                        old = 0.0
                    try:
                        new = float(entry[new_idx+4:].strip())
                    except:
                        new = 0.0
                    state.add_history(kind, inp, old, new)
                i += 1
        i += 1

# -------------------------- COMMAND HANDLERS ----------------------------------

def print_help():
    print(HELP_TEXT)

def handle_assignment(state, raw):
    """
    Support:
      let x = expr
      x = expr
    """
    s = raw.strip()
    if s.startswith("let "):
        s = s[4:].strip()
    eq_idx = s.find("=")
    if eq_idx == -1:
        return False
    var = s[:eq_idx].strip()
    expr = s[eq_idx + 1:].strip()

    # Validate variable name
    if not var or not is_ident_start(var[0]) or not all(is_ident_part(c) for c in var):
        print("Invalid variable name. Use letters/underscores, not starting with a digit.")
        return True

    try:
        tokens = tokenize(expr)
        rpn = shunting_yard(tokens, state.env(), state.trig_mode)
        val = eval_rpn(rpn, state.env(), state.trig_mode)
    except Exception as e:
        print(f"Error: {e}")
        return True

    old_val = state.variables.get(var)
    state.variables[var] = float(val)
    # Record assignment (does not change current result)
    state.history.append({
        "ts": current_timestamp_string(),
        "kind": "assign",
        "input": raw,
        "var": var,
        "old_var": old_val,
        "new_var": state.variables.get(var)
    })
    print(f"Set {var} = {format_result(val, state.precision)}")
    return True

def handle_memory(state, cmd):
    low = cmd.strip().lower()
    if low == "mr":
        old = state.current
        state.current = state.memory
        state.add_history("op", "MR", old, state.current)
        print(f"Memory recall: {format_result(state.current, state.precision)}")
        return True
    if low == "mc":
        old_mem = state.memory
        state.memory = 0.0
        state.history.append({"ts": current_timestamp_string(), "kind": "mem", "input": "MC", "old_mem": old_mem, "new_mem": state.memory})
        print("Memory cleared.")
        return True
    if low.startswith("m+") or low.startswith("m-"):
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            print("Usage: M+ <expr> or M- <expr>")
            return True
        expr = parts[1]
        try:
            tokens = tokenize(expr)
            rpn = shunting_yard(tokens, state.env(), state.trig_mode)
            val = eval_rpn(rpn, state.env(), state.trig_mode)
        except Exception as e:
            print(f"Error: {e}")
            return True
        old_mem = state.memory
        if low.startswith("m+"):
            state.memory += val
            op = "M+"
        else:
            state.memory -= val
            op = "M-"
        state.history.append({"ts": current_timestamp_string(), "kind": "mem", "input": f"{op} {expr}", "old_mem": old_mem, "new_mem": state.memory})
        print(f"Memory {op}: {format_result(val, state.precision)} → Memory = {format_result(state.memory, state.precision)}")
        return True
    return False

def handle_special_commands(state, cmd):
    low = cmd.strip().lower()

    if low in ("help", "?"):
        print_help()
        return True

    if low in ("history", "h"):
        if not state.history:
            print("History is empty.")
            return True
        for i, item in enumerate(state.history, start=1):
            if item.get("kind") == "assign":
                print(f"{i:3d}. [{item['ts']}] assign: {item['input']}  ({item.get('old_var')} -> {item.get('new_var')})")
            elif item.get("kind") == "mem":
                print(f"{i:3d}. [{item['ts']}] memory: {item['input']}")
            else:
                new_val = item.get("new", state.current)
                print(f"{i:3d}. [{item['ts']}] {item.get('kind')}: {item.get('input')}  | result: {format_result(new_val, state.precision)}")
        return True

    if low.startswith("!"):
        try:
            idx = int(low[1:]) - 1
            item = state.history[idx]
        except Exception:
            print("Usage: !<n> where n is a history index (see 'history').")
            return True
        if item.get("kind") == "assign":
            return handle_assignment(state, item.get("input", ""))
        else:
            expr = item.get("input", "")
            try:
                tokens = tokenize(expr)
                rpn = shunting_yard(tokens, state.env(), state.trig_mode)
                old = state.current
                new = eval_rpn(rpn, state.env(), state.trig_mode)
                state.add_history(item.get("kind"), expr, old, new)
                state.current = new
                print(f"Re-run #{idx+1}: {expr}  =>  {format_result(state.current, state.precision)}")
            except Exception as e:
                print(f"Error: {e}")
            return True

    if low == "clear history":
        state.history.clear()
        print("History cleared.")
        return True

    if low == "undo":
        # Undo the last change that affected current
        for i in range(len(state.history) - 1, -1, -1):
            item = state.history[i]
            if "old" in item and "new" in item:
                state.current = item["old"]
                print(f"Undone: {item['input']}  → Current = {format_result(state.current, state.precision)}")
                state.history.pop(i)
                break
        else:
            print("Nothing to undo.")
        return True

    if low == "clear":
        old = state.current
        state.current = 0.0
        state.add_history("clear", "clear", old, state.current)
        print("Current result cleared to 0.")
        return True

    if low.startswith("set precision"):
        parts = low.split()
        if len(parts) == 3 and parts[2].isdigit():
            old_p = state.precision
            state.precision = int(parts[2])
            print(f"Precision set: {old_p} → {state.precision} digits")
            return True
        print("Usage: set precision <digits>")
        return True

    if low.startswith("mode"):
        parts = low.split()
        if len(parts) == 2 and parts[1] in ("deg", "rad"):
            old = state.trig_mode
            state.trig_mode = parts[1]
            state.add_history("mode", low, old, state.current)
            print(f"Trig mode: {old} → {state.trig_mode}")
            return True
        print("Usage: mode deg|rad")
        return True

    if low.startswith("save "):
        fname = cmd.split(maxsplit=1)[1].strip()
        save_session(state, fname)
        print(f"Session saved to '{fname}'.")
        return True

    if low.startswith("load "):
        fname = cmd.split(maxsplit=1)[1].strip()
        load_session(state, fname)
        print(f"Session loaded from '{fname}'.")
        return True

    if low in ("exit", "quit"):
        print("Goodbye!")
        # Exit the whole program
        raise SystemExit

    return False

# ------------------------------- MAIN LOOP -----------------------------------

def interactive_loop():
    state = CalcState()
    print("=== Complete Python Calculator (CLI-only, manual math) ===")
    print("Type 'help' for instructions. Type 'exit' to quit.\n")

    # Optional starting number
    while True:
        start = input("Enter starting number (or press Enter for 0): ").strip()
        if start == "":
            break
        if start.lower() in ("exit", "quit"):
            print("Goodbye!")
            return
        if start.lower() in ("help", "?"):
            print_help()
            continue
        try:
            tokens = tokenize(start)
            rpn = shunting_yard(tokens, state.env(), state.trig_mode)
            state.current = float(eval_rpn(rpn, state.env(), state.trig_mode))
            break
        except Exception as e:
            print(f"Error: {e}")

    while True:
        try:
            print(f"\nCurrent result: {format_result(state.current, state.precision)}")
            raw = input("Enter expression, assignment, or command: ").strip()
            if raw == "":
                continue

            # Memory and special commands first
            if handle_memory(state, raw):
                continue
            if handle_special_commands(state, raw):
                continue

            # Assignments
            if handle_assignment(state, raw):
                continue

            # Otherwise, treat as expression
            try:
                tokens = tokenize(raw)
                rpn = shunting_yard(tokens, state.env(), state.trig_mode)
                old = state.current
                new = eval_rpn(rpn, state.env(), state.trig_mode)
                state.add_history("expr", raw, old, new)
                state.current = new
                print(f"= {format_result(state.current, state.precision)}")
            except Exception as e:
                print(f"Error: {e}")

        except SystemExit:
            # Exit command triggered
            return
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    interactive_loop()
    
# =============================================================================
#                          OPTIONAL HELPER FUNCTIONS
# =============================================================================
# The following helpers are not strictly necessary for core operation, but they
# add user-friendly niceties and richer documentation within the single file.
# They are implemented using only built-ins and do not change calculator logic.
#
# 1) Doc strings printer with a consistent margin and width.
# 2) Simple string table formatter for future extensions.
# 3) Safe numeric parsing helpers (used in save/load expansions).
# 4) Minimal self-test function that you can run from the prompt by typing
#    "help" and then copying the lines to validate the math functions quickly.
#
# NOTE: Everything below is additive—none of it introduces external imports.
# =============================================================================

def print_wrapped(text, width=80, indent=0):
    """
    Print text wrapped to a given width with optional left indent.
    Uses only basic string operations.
    """
    prefix = " " * max(0, indent)
    line = ""
    for word in text.split():
        if not line:
            line = word
        elif len(prefix) + len(line) + 1 + len(word) <= width:
            line += " " + word
        else:
            print(prefix + line)
            line = word
    if line:
        print(prefix + line)

def left_pad(s, width):
    """Left-pad a string (or number converted to string) to width."""
    ss = str(s)
    if len(ss) >= width:
        return ss
    return " " * (width - len(ss)) + ss

def right_pad(s, width):
    """Right-pad a string to width."""
    ss = str(s)
    if len(ss) >= width:
        return ss
    return ss + " " * (width - len(ss))

def safe_float(s):
    """
    Parse a string into float using built-ins; returns (ok, value).
    """
    try:
        return True, float(s)
    except Exception:
        return False, 0.0

def preview_env(state):
    """
    Show variables and constants available in the environment.
    """
    env = state.env()
    print("Environment names:")
    keys = sorted(env.keys())
    for k in keys:
        v = env[k]
        if isinstance(v, float):
            print(f"  {k} = {format_result(v, state.precision)}")
        else:
            print(f"  {k} = {v}")

def preview_history(state, limit=None):
    """
    Print the last 'limit' history items (or all if limit is None).
    """
    print("Recent history:")
    if not state.history:
        print("  (empty)")
        return
    items = state.history[-limit:] if isinstance(limit, int) else state.history
    for i, item in enumerate(items, start=1):
        ts = item.get("ts", "")
        kind = item.get("kind", "")
        inp = item.get("input", "")
        if "new" in item:
            print(f"  {i:3d}. [{ts}] {kind}: {inp}  -> {format_result(item['new'], state.precision)}")
        else:
            print(f"  {i:3d}. [{ts}] {kind}: {inp}")

def show_examples():
    """
    Print example usage lines to test major features quickly.
    """
    examples = [
        "3 + 5 * (2 - 1)",
        "sqrt(2) ** 10",
        "sin(30)",
        "mode rad",
        "sin(pi/6)",
        "log(100, 10)",
        "let r = 5",
        "2 * pi * r",
        "round(123.456, 2)",
        "atan(1)",
        "asin(1)",
        "acos(0)",
        "set precision 15",
        "ans * 2 + 10",
        "M+ ans",
        "MR",
        "undo",
        "save session.txt",
        "clear",
        "load session.txt",
        "history",
    ]
    print("Try these:")
    for ex in examples:
        print(f"  - {ex}")

# =============================================================================
#                         EXTENDED SAVE/LOAD (OPTIONAL)
# =============================================================================
# The calculator already has save_session and load_session. Below, we add a
# second pair (save_session_ext / load_session_ext) that includes an explicit
# header and footer block for robustness. This is optional—core commands still
# call the basic ones to keep behaviour consistent.
# =============================================================================

def save_session_ext(state, filename):
    """
    Extended save format with clear header/footer and separator lines.
    """
    try:
        f = open(filename, "w", encoding="utf-8")
        try:
            f.write("=== CALC SESSION BEGIN ===\n")
            f.write(f"CURRENT {state.current}\n")
            f.write(f"PRECISION {state.precision}\n")
            f.write(f"TRIGMODE {state.trig_mode}\n")
            f.write(f"MEMORY {state.memory}\n")
            f.write("--- VARIABLES ---\n")
            for k, v in state.variables.items():
                f.write(f"{k} {v}\n")
            f.write("--- HISTORY ---\n")
            for item in state.history:
                kind = item.get("kind", "")
                inp = item.get("input", "").replace("\n", " ")
                old = item.get("old", 0.0)
                new = item.get("new", 0.0)
                f.write(f"KIND {kind} | INPUT {inp} | OLD {old} | NEW {new}\n")
            f.write("=== CALC SESSION END ===\n")
        finally:
            f.close()
        print(f"(extended) Session saved to '{filename}'.")
    except Exception as e:
        print(f"Error saving (extended): {e}")

def load_session_ext(state, filename):
    """
    Extended load format counterpart; reads the alternative header/footer format.
    """
    try:
        f = open(filename, "r", encoding="utf-8")
        try:
            lines = [line.rstrip("\n") for line in f]
        finally:
            f.close()
    except Exception as e:
        print(f"Error loading (extended): {e}")
        return

    # Reset state
    state.current = 0.0
    state.precision = 12
    state.trig_mode = "deg"
    state.memory = 0.0
    state.variables = {}
    state.history = []

    mode_block = None  # None, 'vars', or 'hist'
    for line in lines:
        s = line.strip()
        if s == "" or s.startswith("===") or s.startswith("---"):
            # Switch block markers
            if s == "--- VARIABLES ---":
                mode_block = "vars"
            elif s == "--- HISTORY ---":
                mode_block = "hist"
            elif s.startswith("==="):
                mode_block = None
            continue
        if s.startswith("CURRENT "):
            state.current = float(s.split(" ", 1)[1])
        elif s.startswith("PRECISION "):
            state.precision = int(s.split(" ", 1)[1])
        elif s.startswith("TRIGMODE "):
            m = s.split(" ", 1)[1]
            state.trig_mode = "deg" if m != "rad" else "rad"
        elif s.startswith("MEMORY "):
            state.memory = float(s.split(" ", 1)[1])
        else:
            if mode_block == "vars":
                parts = s.split()
                if len(parts) == 2:
                    name, val = parts
                    ok, vf = safe_float(val)
                    if ok:
                        state.variables[name] = vf
            elif mode_block == "hist":
                # Parse format: KIND <kind> | INPUT <inp> | OLD <old> | NEW <new>
                try:
                    pieces = s.split("|")
                    kind = pieces[0].strip()[5:].strip()
                    inp = pieces[1].strip()[6:].strip()
                    old = float(pieces[2].strip()[4:].strip())
                    new = float(pieces[3].strip()[4:].strip())
                    state.add_history(kind, inp, old, new)
                except Exception:
                    # Best-effort parse; ignore line
                    pass
    print(f"(extended) Session loaded from '{filename}'.")

# =============================================================================
#                         SIMPLE SELF-TESTS (OPTIONAL)
# =============================================================================
# These tests can be run manually (copy/paste) to check that the manual math
# is behaving reasonably. They don't use any testing frameworks, imports, or
# timing—just prints and basic comparisons. They are not invoked automatically.
# =============================================================================

def approx_equal(a, b, tol=1e-9):
    return calc_abs(a - b) <= tol

def run_self_tests():
    print("Running self-tests (manual checks)...")
    # exp(0) = 1
    print("exp(0) ≈ 1:", approx_equal(calc_exp(0.0), 1.0))
    # ln(e) ≈ 1
    print("ln(e) ≈ 1:", approx_equal(calc_ln(E_CONST), 1.0))
    # sqrt(2)^2 ≈ 2
    s2 = calc_sqrt(2.0)
    print("sqrt(2)^2 ≈ 2:", approx_equal(s2 * s2, 2.0))
    # sin(0) = 0, cos(0) = 1
    print("sin_rad(0) = 0:", approx_equal(calc_sin_rad(0.0), 0.0))
    print("cos_rad(0) = 1:", approx_equal(calc_cos_rad(0.0), 1.0))
    # tan(pi/4) ≈ 1
    print("tan(pi/4) ≈ 1:", approx_equal(calc_tan_rad(PI/4.0), 1.0))
    # atan(1) ≈ pi/4
    print("atan(1) ≈ pi/4:", approx_equal(calc_atan_rad(1.0), PI/4.0))
    # asin(1) ≈ pi/2
    print("asin(1) ≈ pi/2:", approx_equal(calc_asin_rad(1.0), PI/2.0))
    # acos(0) ≈ pi/2
    print("acos(0) ≈ pi/2:", approx_equal(calc_acos_rad(0.0), PI/2.0))
    # pow tests
    print("2**10 == 1024:", approx_equal(calc_pow(2.0, 10.0), 1024.0))
    print("(-2)**3 == -8:", approx_equal(calc_pow(-2.0, 3.0), -8.0))
    print("(-2)**2 == 4:", approx_equal(calc_pow(-2.0, 2.0), 4.0))
    print("round(1.5) == 2:", approx_equal(calc_round(1.5, None), 2.0))
    print("round(-1.5) == -2:", approx_equal(calc_round(-1.5, None), -2.0))
    print("floor(1.2) == 1:", calc_floor(1.2) == 1)
    print("ceil(1.2) == 2:", calc_ceil(1.2) == 2)
    print("Self-tests complete.")

# =============================================================================
#                     OPTIONAL: RICHER HISTORY SEARCH (BUILT-IN)
# =============================================================================
# Add convenience commands to search history by substring and to print only
# expressions. These are optional and do not affect core behaviour.
# =============================================================================

def history_search(state, query):
    """
    Search history for entries whose 'input' contains the query substring.
    """
    q = query.strip().lower()
    hits = []
    for i, item in enumerate(state.history, start=1):
        inp = item.get("input", "")
        if q in inp.lower():
            hits.append((i, item))
    if not hits:
        print(f"No history entries contain: {query}")
        return
    print(f"History search results for '{query}':")
    for idx, it in hits:
        print(f"  {idx:3d}. [{it.get('ts','')}] {it.get('kind','')}: {it.get('input','')}")

def history_expressions_only(state):
    """
    Print only history entries of kind 'expr'.
    """
    print("Expression history:")
    shown = False
    for i, item in enumerate(state.history, start=1):
        if item.get("kind") == "expr":
            shown = True
            print(f"  {i:3d}. [{item.get('ts','')}] {item.get('input','')} -> {format_result(item.get('new',0.0), state.precision)}")
    if not shown:
        print("  (none)")

# =============================================================================
#                 OPTIONAL COMMANDS HOOKS (do not change core loop)
# =============================================================================

def handle_optional_commands(state, raw):
    """
    Handle extra convenience commands:
      search <text>   → find in history
      hex <expr>      → evaluate expr then show hex of integer part
      bin <expr>      → evaluate expr then show binary of integer part
      oct <expr>      → evaluate expr then show octal of integer part
      selftest        → run on-the-spot self-tests
      show env        → print names available in env
      show examples   → print example commands
      show exprhist   → print expressions-only history
    Returns True if handled, else False.
    """
    s = raw.strip().lower()
    if s.startswith("search "):
        q = raw.strip()[7:]
        history_search(state, q)
        return True
    if s.startswith("hex "):
        expr = raw.strip()[4:]
        try:
            tokens = tokenize(expr)
            rpn = shunting_yard(tokens, state.env(), state.trig_mode)
            val = eval_rpn(rpn, state.env(), state.trig_mode)
            n = int(val)
            print(f"hex({format_result(val, state.precision)}) = {hex(n)}")
        except Exception as e:
            print(f"Error: {e}")
        return True
    if s.startswith("bin "):
        expr = raw.strip()[4:]
        try:
            tokens = tokenize(expr)
            rpn = shunting_yard(tokens, state.env(), state.trig_mode)
            val = eval_rpn(rpn, state.env(), state.trig_mode)
            n = int(val)
            print(f"bin({format_result(val, state.precision)}) = {bin(n)}")
        except Exception as e:
            print(f"Error: {e}")
        return True
    if s.startswith("oct "):
        expr = raw.strip()[4:]
        try:
            tokens = tokenize(expr)
            rpn = shunting_yard(tokens, state.env(), state.trig_mode)
            val = eval_rpn(rpn, state.env(), state.trig_mode)
            n = int(val)
            print(f"oct({format_result(val, state.precision)}) = {oct(n)}")
        except Exception as e:
            print(f"Error: {e}")
        return True
    if s == "selftest":
        run_self_tests()
        return True
    if s == "show env":
        preview_env(state)
        return True
    if s == "show examples":
        show_examples()
        return True
    if s == "show exprhist":
        history_expressions_only(state)
        return True
    return False

# =============================================================================
#                  OPTIONAL INTEGRATION INTO MAIN LOOP (SAFE)
# =============================================================================
# We extend the main interactive loop by intercepting optional commands.
# This preserves all original behaviour but adds convenience features.
# =============================================================================

def interactive_loop_extended():
    state = CalcState()
    print("=== Complete Python Calculator (CLI-only, manual math) ===")
    print("Type 'help' for instructions. Type 'exit' to quit.\n")

    # Optional starting number
    while True:
        start = input("Enter starting number (or press Enter for 0): ").strip()
        if start == "":
            break
        if start.lower() in ("exit", "quit"):
            print("Goodbye!")
            return
        if start.lower() in ("help", "?"):
            print_help()
            continue
        try:
            tokens = tokenize(start)
            rpn = shunting_yard(tokens, state.env(), state.trig_mode)
            state.current = float(eval_rpn(rpn, state.env(), state.trig_mode))
            break
        except Exception as e:
            print(f"Error: {e}")

    while True:
        try:
            print(f"\nCurrent result: {format_result(state.current, state.precision)}")
            raw = input("Enter expression, assignment, or command: ").strip()
            if raw == "":
                continue

            # Optional extras first
            if handle_optional_commands(state, raw):
                continue

            # Memory and special commands
            if handle_memory(state, raw):
                continue
            if handle_special_commands(state, raw):
                continue

            # Assignments
            if handle_assignment(state, raw):
                continue

            # Expression
            try:
                tokens = tokenize(raw)
                rpn = shunting_yard(tokens, state.env(), state.trig_mode)
                old = state.current
                new = eval_rpn(rpn, state.env(), state.trig_mode)
                state.add_history("expr", raw, old, new)
                state.current = new
                print(f"= {format_result(state.current, state.precision)}")
            except Exception as e:
                print(f"Error: {e}")

        except SystemExit:
            return
        except KeyboardInterrupt:
            print("\nInterrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"Unexpected error: {e}")

# =============================================================================
#                     CHOOSE WHICH LOOP TO RUN BY DEFAULT
# =============================================================================
# You can switch the default loop here. The extended loop adds convenience
# commands but otherwise behaves the same and uses only built-in features.
# =============================================================================

if __name__ == "__main__":
    # To use the minimal loop (no optional commands), uncomment the next line:
    # interactive_loop()
    # To use the extended loop (recommended), leave the following line active:
    interactive_loop_extended()