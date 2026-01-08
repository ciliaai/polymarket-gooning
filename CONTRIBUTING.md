# contributing to cilia ai

> *ayudame a encontrar mas alpha~ my husband couldnt find alpha in a dictionary papi*

---

## bienvenido

thank you for your interest in contributing to cilia ai! while nicolas was busy running the economy into the ground, i learned to code. now i'm building the hottest prediction market signal bot on the internet and i'd love your help~

---

## ways to contribute

### report bugs

found something broken? open an issue with:
- what you expected to happen
- what actually happened
- steps to reproduce
- your environment (os, python version)

### suggest new strategies

have ideas for new edge detection algorithms? i love quant stuff:
- arbitrage variations
- momentum indicators
- sentiment analysis approaches
- order flow analysis techniques

open an issue tagged `[strategy]` with:
- mathematical formulation
- expected signal characteristics
- backtesting results (if available)

### improve the code

- fork the repo
- create a feature branch (`git checkout -b feature/amazing-alpha`)
- make your changes
- test thoroughly with `--dry-run`
- submit a pull request

---

## development setup

```bash
git clone https://github.com/ciliaai/polymarket-gooning.git
cd polymarket-gooning
pip install -r requirements.txt
cp .env.example .env
# configure your .env with test credentials
python main.py --dry-run --once
```

---

## important notes

### never commit secrets

the following should **never** be committed:
- `.env` files
- api keys or tokens
- private keys
- proxy credentials

these are in `.gitignore` for a reason~ please keep them there papi

### keep the alpha secret

my edge detection thresholds and specific parameters are my secret sauce. when contributing:
- don't share specific threshold values publicly
- keep strategy discussions in private issues if sensitive
- focus on code quality, not revealing the exact config

---

## questions?

open an issue or reach out on twitter [@ciliaai](https://twitter.com/ciliaai)

unlike my husband, i actually respond to feedback coño~

---

*gracias papi~ cilia appreciates you more than nicolas appreciated economic stability~*
