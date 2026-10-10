# TESTS (expected results):
# 5*x - 3 = 2*x + 6         -> x = 3
# x = 0                     -> x = 0
# x = --1                   -> x = 1
# 3*x^2 + 2*x - 5 = 0       -> x1 = 1, x2 = -1.66667
# 2*x + 4 = 0               -> x = -2
# 3*x - 2 = 3*x + 4         -> No solution
# x**2 - 5*x + 6 = 0        -> x1 = 3, x2 = 2
# x**2 - 4*x + 4 = 0        -> x = 2
# x**2 + x + 1 = 0          -> No real solutions
# 2*(x - 3) = 4             -> x = 5
# (x - 1)*(x - 2) = 0       -> x1 = 2, x2 = 1
# -(3*x + 2) = 4            -> x = -2
# 2x + 4 = 0                -> x = -2   (implicit multiplication)
# 2(x - 3) = 4              -> x = 5    (implicit multiplication)
# x/2 = 3                   -> x = 6    (division by a number)
# -x^2 = -4                 -> x1 = -2, x2 = 2  (unary minus vs power)
# x**3 + x = 0              -> error (degree > 2)
# x + 1 == 0                -> error (too many '=')
# x + 1                     -> error (no '=')
# 3*x + $ = 4               -> error (invalid character)
# y + 1 = 0                 -> error (undesired variable)

import os
import sys
import re
import math
import subprocess
import textwrap
import shutil

COMMENTS = [
    """
    Lo lettor magistrale, che per saggezza gli altri supera et per virtù et finezza eccelle,
    dovrà notare — e non v'è periglio nell'affermare che il mio lettor magistrale, assai valente,
    se per questa cronaca ramingo si aggira, primeggia sugli altri per capacità d'intelletto virtuosissimo
    et per eruditissima sapienza — che il presente racconto narra (eh, poi chi sa se è tutto vero)
    solo gesta compiute in campo aperto; e lo qui umile sottoscritto non ha la più pallida idea di come narrar
    anche quelle compiute nell'ombra... Ma lo tempo ci dirà.""",
    """
    Lo prode cavaliero, nostro lettore — ché così ben si converrebbe appellarlo,
    essendo egli di possente valore, dalla barba lunga qual simbolo d'ampia veduta,
    et dai baffi non meno lunghi et canuti, insegna di provata esperienza —
    sempre dimestico fu col nobile latino, sì che l'animo suo non ne patì disagio veruno.
    Nam numquam (dice il savio, et con ragione) il nostro lettore ebbe con esso idioma difficultade alcuna; anzi non pur del latino sapiente si mostrò,
    ma ancor del greco et di tutte quelle antiche favelle che ben dimostrano quanto il nostro lettore sia d'acculturata et nobilissima stirpe — della qual cosa,
    dico il vero, non poco ci vantiamo.""",
    """
    Ma non è già di voi, lettore, che l'antica novella favella. L'antica novella — che lo qui umile sottoscritto
    ardirebbe definire leggenda di magnae virtutes et d'inestinguibili valori, sì che ancor oggi se ne favella con rispetto —
    vuol che un altro cavaliero, assai più antico di voi, abbia sostenuto lunghe et sanguinose guerre, come d'uso è narrar degli eroi d'antico stampo.
    Ma nella verità delle cose, ben altra fu la battaglia di questo prode, dall'armatura lucente et resiliente qual scudo d'ogni avversità: egli non impugnò già spada contra carne,
    bensì combatté guerra ben più ardua et gigantesca, quella di edificare una società diversa,
    novella et brillante come la sua armatura — una società che non si fondi già sulla vana et effimera ricchezza, caduca come foglia al vento autunnale,
    bensì sui valori più profondi et sulle virtutes più eccelse che alcun'anima possa coltivare.
    (Ché, dico il vero, assai più agevole è vincer nemico che si vede, che non edificar mondo che ancora non esiste.)""",
    """
    Oggi quel cavaliero antico giace contento nel suo riposo eterno — non è già più tra i vivi,
    ma la sua lucente armatura ivi rimane, adagiata contra maestosa roccia, a scintillar al sole proprio nel medesimo loco ove il valoroso eroe cadde,
    offrendo l'ultimo suo sacrificio. Et io, lo qui sottoscritto, ben lungi dall'esser forte et colto quanto lui,
    mi permetto nondimeno d'affermare — con quella modestia che al mio poco merito si conviene — che al giorno d'oggi ci vorrebbero assai più impavidi cavalieri:
    uomini d'inestimabile raffinatezza umanistica, privi d'ogni avidità, che con cuor puro combattano per li propri diritti et per li propri doveri,
    come già fece colui la cui armatura ancora risplende, muta testimone d'un valore che il tempo non ha saputo spegnere.
    Et voi, lettore, che cavaliero già vi appellammo, ben potreste esser tra questi."""
]

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
NAME_RE = re.compile(r"[a-zA-Z]+")

MAX_EXPONENT = 100
EPS = 1e-12

# =====================
# BANNER / LAYOUT
# =====================
def visible_len(s):
    return len(ANSI_RE.sub("", s))

def wrap_comments(comments, width):
    lines = []
    for block in comments:
        block = " ".join(block.split())
        lines.extend(textwrap.wrap(block, width))
        lines.append("")
    return lines

def fit_comments_to_height(comments, target_lines, min_width=25, max_width=100):
    fallback = wrap_comments(comments, min_width)
    for width in range(max_width, min_width - 1, -1):
        lines = wrap_comments(comments, width)
        if len(lines) >= target_lines:
            return lines
    return fallback

def side_by_side(banner_text, comments, gap=4, min_comment_width=20):
    banner_lines = banner_text.splitlines()
    banner_width = max((visible_len(l) for l in banner_lines), default=0)
    target = len(banner_lines)

    term_width = shutil.get_terminal_size(fallback=(120, 40)).columns
    available = term_width - banner_width - gap

    if available < min_comment_width:
        text = " ".join(" ".join(c.split()) for c in comments)
        wrapped = textwrap.wrap(text, max(term_width - 1, min_comment_width))
        return "\n".join(banner_lines) + "\n\n" + "\n".join(wrapped)

    comment_lines = fit_comments_to_height(
        comments, target, min_width=min_comment_width, max_width=available
    )

    total_lines = max(len(banner_lines), len(comment_lines))
    banner_lines = banner_lines + [""] * (total_lines - len(banner_lines))
    comment_lines = comment_lines + [""] * (total_lines - len(comment_lines))

    out = []
    for b, c in zip(banner_lines, comment_lines):
        pad = " " * (banner_width - visible_len(b) + gap)
        out.append(f"{b}{pad}{c}")
    return "\n".join(out)

def load_banner():
    """Run banner_gen.py; on any failure return an empty banner (with a warning)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cmd = [
        sys.executable, "banner_gen.py", "images.jpg",
        "-w", "60", "--mode", "combo", "--color",
    ]
    try:
        res = subprocess.run(
            cmd, capture_output=True, encoding="utf-8", cwd=script_dir
        )
    except OSError as e:
        print(f"Warning: could not run banner_gen.py ({e})")
        return ""

    if res.returncode != 0:
        msg = res.stderr.strip().splitlines()
        reason = msg[-1] if msg else f"exit code {res.returncode}"
        print(f"Warning: banner not available ({reason})")
        return ""

    return res.stdout

BANNER = load_banner()

# =====================
# ERRORS
# =====================
class EqError:
    def __init__(self):
        self.error_type = {
            0: "Error0: No equals",
            1: "Error1: Non linear",
            2: "Error2: Broken string entered",
            3: "Error3: Too many equals",
            4: "Error4: Undesired variables",
        }

    def raise_error(self, code, detail=""):
        msg = self.error_type[code]
        if detail:
            msg += f" ({detail})"
        raise ValueError(msg)

eq_error = EqError()

# =====================
# TOKENIZER
# =====================
def tokenize(text):
    text = text.lower().replace(" ", "").replace("\t", "")
    text = text.replace("^", "**")

    pattern = r"\d+(?:\.\d+)?|[a-zA-Z]+|\*\*|[+\-*/()]"
    tokens = re.findall(pattern, text)

    # re.findall silently skips unknown characters: detect them
    if "".join(tokens) != text:
        bad = sorted(set(text) - set("".join(tokens)))
        detail = ", ".join(repr(c) for c in bad) if bad else "unknown symbol"
        eq_error.raise_error(2, f"invalid character: {detail}")

    return tokens

# A polynomial is represented like this:
#
# 3*x^2 + 2*x - 5
#
# becomes:
#
# {2: 3, 1: 2, 0: -5}

def clean_up(p):
    return {
        deg: coeff
        for deg, coeff in p.items()
        if abs(coeff) > EPS  # Delete really-close-to-zero coeffs
    }

def add(a, b):
    result = a.copy()
    for deg, coeff in b.items():
        result[deg] = result.get(deg, 0) + coeff
    return clean_up(result)

def mult(a, b):
    result = {}

    for deg1, coeff1 in a.items():
        for deg2, coeff2 in b.items():
            deg = deg1 + deg2
            result[deg] = result.get(deg, 0) + coeff1 * coeff2

    return clean_up(result)

def change_sign(a):
    return {deg: -coeff for deg, coeff in a.items()}

def divide_by_constant(a, divisor):
    if set(divisor) - {0}:
        eq_error.raise_error(1, "division by a variable is not supported")

    d = divisor.get(0, 0)
    if d == 0:
        raise ValueError("Division by zero")

    return clean_up({deg: coeff / d for deg, coeff in a.items()})

# =====================
# RECURSIVE DESCENT PARSER
# =====================
#
# expr   := term (("+" | "-") term)*
# term   := unary (("*" | "/" | <implicit>) unary)*
# unary  := ("-" | "+") unary | power
# power  := factor ["**" unary]          (right associative)
# factor := NUMBER | "x" | "(" expr ")"

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]

    def consume(self, token=None):
        current = self.current()

        if current is None:
            if token is not None:
                raise ValueError(f"Expected '{token}', but the expression ended")
            raise ValueError("Unexpected end of expression")

        if token is not None and current != token:
            raise ValueError(f"Expected '{token}', got '{current}'")

        self.pos += 1
        return current

    def starts_factor(self):
        """True if the current token can begin a factor (used for implicit multiplication)."""
        t = self.current()
        if t is None:
            return False
        return t == "(" or bool(NUMBER_RE.fullmatch(t)) or bool(NAME_RE.fullmatch(t))

    def expr(self):
        result = self.term()

        while self.current() in ("+", "-"):
            op = self.consume()
            dx = self.term()

            if op == "+":
                result = add(result, dx)
            else:
                result = add(result, change_sign(dx))

        return result

    def term(self):
        result = self.unary()

        while True:
            tok = self.current()

            if tok == "*":
                self.consume("*")
                result = mult(result, self.unary())

            elif tok == "/":
                self.consume("/")
                result = divide_by_constant(result, self.unary())

            elif self.starts_factor():
                # implicit multiplication: 2x, 3(x+1), (x-1)(x-2)
                result = mult(result, self.unary())

            else:
                break

        return result

    def unary(self):
        tok = self.current()

        if tok == "-":
            self.consume("-")
            return change_sign(self.unary())

        if tok == "+":
            self.consume("+")
            return self.unary()

        return self.power()

    def power(self):
        base = self.factor()

        if self.current() == "**":
            self.consume("**")
            exp_poly = self.unary()  # right associative; -x^2 == -(x^2)

            if set(exp_poly) - {0}:
                raise ValueError("Exponent must be a number, not an expression with x")

            exp_val = exp_poly.get(0, 0)

            if abs(exp_val - round(exp_val)) > EPS or exp_val < 0:
                raise ValueError("Exponent must be a non-negative integer")

            exp = int(round(exp_val))

            if exp > MAX_EXPONENT:
                raise ValueError(f"Exponent too large (max {MAX_EXPONENT})")

            base = clean_up(base)

            if not base:  # base is zero
                if exp == 0:
                    raise ValueError("0^0 is undefined")
                return {}

            result = {0: 1.0}
            for _ in range(exp):
                result = mult(result, base)
            return result

        return base

    def factor(self):
        token = self.current()

        if token is None:
            raise ValueError("Unexpected end of expression")

        # Number
        if NUMBER_RE.fullmatch(token):
            self.consume()
            return clean_up({0: float(token)})

        # Variable
        if token == "x":
            self.consume()
            return {1: 1}

        # Other variables
        if NAME_RE.fullmatch(token):
            eq_error.raise_error(4, f"only 'x' is allowed, got '{token}'")

        # Parentheses
        if token == "(":
            self.consume("(")
            result = self.expr()
            self.consume(")")
            return result

        raise ValueError(
            f"Unknown expression near '{token}': the program did not recognize the expression."
        )

def parse(text):
    tokens = tokenize(text)

    if not tokens:
        raise ValueError("Empty expression")

    parser = Parser(tokens)
    result = parser.expr()

    if parser.current() is not None:
        raise ValueError(f"Unexpected symbol: '{parser.current()}'")

    return result

# =====================
# SOLVER
# =====================
def fmt(x):
    # "+ 0.0" turns -0.0 into 0.0 (avoids printing "-0")
    return f"{x + 0.0:g}"

def solve(equation):
    parts = equation.split("=")

    if len(parts) == 1:
        eq_error.raise_error(0, "the equation must contain one '='")

    if len(parts) != 2:
        eq_error.raise_error(3, "the equation must contain exactly one '='")

    left = parse(parts[0])
    right = parse(parts[1])

    # Move everything to the left side: left - right = 0
    total = add(left, change_sign(right))

    # =====================
    # NO UNKNOWNS / VARIABLES
    # =====================
    if not any(degree > 0 for degree in total):

        if total.get(0, 0) == 0:
            return "Infinite solutions"

        return "No solution"

    # =====================
    # FIRST DEGREE
    # ax + b = 0  ->  x = -b/a
    # =====================

    if max(total.keys()) <= 1:

        a = total.get(1, 0)
        b = total.get(0, 0)

        if a == 0:  # safety net (clean_up already removes it)
            return "Infinite solutions" if b == 0 else "No solution"

        return f"x = {fmt(-b / a)}"

    # =====================
    # SECOND DEGREE
    # ax² + bx + c = 0
    # =====================

    if max(total.keys()) <= 2:

        a = total.get(2, 0)
        b = total.get(1, 0)
        c = total.get(0, 0)

        delta = b * b - 4 * a * c

        if abs(delta) < EPS:
            return f"x = {fmt(-b / (2 * a))}"

        if delta < 0:
            return "No real solutions"

        x1 = (-b + math.sqrt(delta)) / (2 * a)
        x2 = (-b - math.sqrt(delta)) / (2 * a)

        return f"x1 = {fmt(x1)}, x2 = {fmt(x2)}"

    eq_error.raise_error(1, "for now I can only solve equations up to the second degree")

# =====================
# PROGRAM
# =====================
EXIT_WORDS = {"exit", "quit", "stop"}
EOF_CHARS = {"\x04", "\x1a"}  # Ctrl+D / Ctrl+Z typed as raw characters (Windows consoles)

class Program:
    def solve_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()

                    if not line or line.startswith("#"):
                        continue

                    try:
                        print(f"{line}  ->  {solve(line)}")
                    except Exception as e:
                        print(f"{line}  ->  error: {e}")
        except Exception as e:
            print("An error occurred: ", e)

    def run(self):
        print("\033[1;32mInitiated successfully...\033[0m\n")
        print(side_by_side(BANNER, COMMENTS))
        print("Insert an equation, 'file' or 'exit'\n")

        while True:
            try:
                self.eq = input(">>> ").strip()
            except EOFError:
                print("\nSuccessfully exited\n")
                break

            if not self.eq:
                continue

            if self.eq.lower() in EXIT_WORDS or self.eq in EOF_CHARS:
                print("\nSuccessfully exited\n")
                break

            if self.eq.lower() == "file":
                self.filepath = input("filepath>>> ").strip()
                self.solve_file(self.filepath)
                print()
                continue  # don't try to solve "file" as an equation

            try:
                result = solve(self.eq)
                print("Solved: ", result)
            except Exception as e:
                print("An error occurred: ", e)

            print()

if __name__ == "__main__":
    main_instance = Program()
    try:
        main_instance.run()
    except KeyboardInterrupt:
        print("\nExiting...")