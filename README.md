<div align="center">

# xmarks

**X marks the spot.** A command-line solver for first and second degree equations in `x`.

![Version](https://img.shields.io/badge/version-1.1.0-purple)
![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Degree](https://img.shields.io/badge/solves-1st%20%26%202nd%20degree-orange)

</div>

Type an equation the way you would write it on paper, get the real solutions.

```
>>> 5*x - 3 = 2*x + 6
Solved:  x = 3

>>> x**2 - 5*x + 6 = 0
Solved:  x1 = 3, x2 = 2

>>> 2(x - 3) = 4
Solved:  x = 5
```

No `eval()`, no algebra libraries: a hand-written recursive descent parser turns the equation into a polynomial and solves it.

---

## Quick start

```bash
git clone https://github.com/ParallelNode/xmarks.git
cd xmarks
python linear_eq.py
```

Requires Python 3.8+. Type an equation and press Enter. Type `exit` to quit.

---

## What you can write

| You can use | Example |
|-------------|---------|
| `+ - * / ^ **` and parentheses | `(x - 1)*(x - 2) = 0` |
| Implicit multiplication | `2x + 4 = 0`, `2(x - 3) = 4` |
| Division by a number | `x/2 = 3` |
| Integer powers, 0 to 100 | `x**2 - 4*x + 4 = 0` |
| Unary minus | `-(3x + 2) = 4`, `-x^2 = -4` |

**Possible results:** one value, two values, `No solution`, `Infinite solutions`, `No real solutions`.

---

## Solve many equations from a file

Type `file` at the prompt, then the path of a text file with one equation per line. Blank lines and lines starting with `#` are ignored.

`equations.txt`

```
# my equations
2x + 4 = 0
x/2 = 3
x**2 + x + 1 = 0
```

```
>>> file
filepath>>> equations.txt
2x + 4 = 0  ->  x = -2
x/2 = 3  ->  x = 6
x**2 + x + 1 = 0  ->  No real solutions
```

A wrong line shows an error and the rest still run.

---

## How it works

```
text  →  tokenizer  →  recursive descent parser  →  polynomial  →  solver
"3x+2=8"   [3, x, +, 2]      expr → term → unary → power → factor     {1: 3, 0: -6}     x = 2
```

Every polynomial is a dictionary `{degree: coefficient}`. Everything on the right of the `=` is moved to the left, then the equation is solved directly (1st degree) or with the discriminant (2nd degree).

---

## Errors

| Code | Cause | Example |
|------|-------|---------|
| `Error0` | no `=` | `x + 1` |
| `Error1` | degree above 2, or division by `x` | `x**3 + x = 0` |
| `Error2` | invalid character | `3x + $ = 4` |
| `Error3` | more than one `=` | `x + 1 == 0` |
| `Error4` | variable other than `x` | `y + 1 = 0` |

---

## Limits

- Only the unknown `x`
- Only real solutions
- Up to degree 2
- Equations are typed at the prompt or read from a file (not passed as command-line arguments)

---

<details>
<summary><b> Optional banner</b></summary>

<br>

On startup the program can show a colored braille-art banner made by `banner_gen.py`. It needs:

```bash
pip install pillow numpy
```

and an image named `images.jpg` next to the scripts (not included). Without them the program works the same and prints a short warning.

`banner_gen.py` also works on its own:

```bash
python banner_gen.py picture.jpg -w 100 --mode combo --color
```

</details>
