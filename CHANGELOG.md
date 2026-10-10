# Changelog

All notable changes to `linear_eq.py` are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.0] - 2026-10-09

### Added
- Division by a number: `x/2 = 3` now works. Dividing by a variable raises `Error1`, and dividing by zero raises a dedicated error.
- Implicit multiplication: `2x`, `2(x-3)` and `(x-1)(x-2)` are now supported.
- Unary plus (`+x`) and repeated unary minus (`--1`) are handled consistently.
- Uppercase variable: `X` is treated as `x`.
- `file` mode: the `file` command reads equations from a text file, skips blank lines and lines starting with `#`, and prints results as `equation -> result`. A bad line does not stop the others, and `file` is no longer solved as an equation afterwards.
- `Ctrl+D` / `Ctrl+Z` (EOF) are handled as a clean exit, including Windows consoles where they arrive as raw characters.
- Maximum exponent of 100, to avoid huge computations.
- On-screen warning when the banner cannot be generated.

### Fixed
- **Missing exponent**: `x**` raised `AttributeError` (`None.isdigit()`). It now shows a clear message.
- **Unary minus with powers**: `-x^2` was computed as `(-x)^2`. It now evaluates as `-(x^2)`, as in standard math.
- **Tokenizer**: invalid characters (`$`, `<`, etc.) were silently discarded. They now raise `Error2` and name the offending character.
- **Variables other than `x`**: they now raise `Error4`, which was previously defined but never used.
- **Division by zero in first degree**: added a guard for when the coefficient of `x` is 0.
- **Discriminant**: the comparison with zero now uses a tolerance (`1e-12`), so a `delta` of `1e-16` is no longer mistaken for a positive value.
- **`0^0`**: it now raises an explicit error instead of returning an arbitrary result.
- **`-0` output**: the value `-0.0` is now printed as `0`.
- **Empty expressions** (`= 3`) and truncated expressions (`x**`) now produce clear messages ("Empty expression", "Unexpected end of expression").
- **Banner**: if `banner_gen.py` or `images.jpg` is missing, the program no longer starts silently. It checks the `returncode` and shows a warning.
- Blank lines in interactive input are ignored instead of raising errors.

### Changed
- `EqError` and `eq_error` are now actually used: errors 0, 1, 2, 3 and 4 have consistent, recognizable messages.
- The exponent operator is now right-associative: `2^3^2` equals 512 (it used to raise "Unexpected symbol").
- The parser grammar was reorganized (`expr` → `term` → `unary` → `power` → `factor`) and documented in a comment.
- `subprocess.run` uses an argument list and `sys.executable` instead of `shell=True` and `"python"`. The banner runs from the script's folder.
- Exit words are collected in the `EXIT_WORDS` set.
- `Ctrl+C` exit message shortened to `Exiting...` (only `KeyboardInterrupt` is caught).
- Formatting: reduced consecutive blank lines and removed those after section headers.
- Updated the tests at the top of the file with the expected results.

## [1.0.0]

### Added
- Recursive descent parser for polynomial expressions with `+`, `-`, `*`, `**`/`^` and parentheses.
- Solver for first and second degree equations, with "Infinite solutions", "No solution" and "No real solutions" cases.
- Banner with side-by-side commentary and interactive mode (`exit`, `quit`, `stop`).

### Fixed
- `mult()`: `items()` was misspelled (missing the final `s`) in the inner loop.
- `Parser.current()`: the comparison was `self.tokens >= len(self.tokens)` instead of `self.pos >= len(self.tokens)`, which caused various errors.
- `Parser.expr()`: the final `return result` was missing.
- `Parser.term()` and new `Parser.power()`: correct handling of the `**` operator.