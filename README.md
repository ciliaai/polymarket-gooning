# cilia ai

> *my husband mass printed bolivars and crashed the economy~ but me? i find alpha. we are not the same papi~*

[![made with love](https://img.shields.io/badge/made%20with-amor-CF142B.svg)](https://twitter.com/ciliaai)
[![more stable than](https://img.shields.io/badge/more%20stable%20than-the%20bolivar-FFCC00.svg)]()
[![nicolas could never](https://img.shields.io/badge/nicolas-could%20never-00247D.svg)]()

---

## que es esto papi

while my husband was busy printing money, blaming the cia, and speedrunning hyperinflation, i was studying the blade (quantitative finance).

cilia ai is my autonomous market intelligence system that applies actual economic knowledge (something nicolas never had) to prediction markets. i use proprietary signal detection algorithms to identify inefficiencies in real-time~ unlike the venezuelan central bank, my signals are actually worth something coño~

---

## the math behind the magic

### kelly criterion optimization

i size my signal confidence using the kelly criterion for optimal bet sizing:

```
f* = (bp - q) / b

where:
  f* = optimal fraction of capital
  b  = odds received on the bet (decimal - 1)
  p  = probability of winning
  q  = probability of losing (1 - p)
```

### information ratio & sharpe decomposition

each signal's quality is measured by its information ratio:

```
IR = E[r_signal - r_benchmark] / σ(r_signal - r_benchmark)

risk-adjusted alpha = IR × σ_target × √(1 - ρ²)
```

### black-scholes adapted for binary outcomes

i model prediction market fair value using modified black-scholes:

```
C = e^(-rT) × N(d₂)

d₂ = [ln(P/K) + (r - σ²/2)T] / (σ√T)

where:
  P = current implied probability
  K = strike (0.5 for fair coin flip)
  σ = historical volatility of the market
  T = time to resolution
```

### order flow toxicity (vpin)

i detect informed trading using volume-synchronized probability of informed trading:

```
VPIN = Σ|V_buy - V_sell| / (n × V_bucket)

toxic flow detected when: VPIN > 0.4
```

### mean reversion via ornstein-uhlenbeck

prices follow a mean-reverting stochastic process:

```
dP = θ(μ - P)dt + σdW

half-life = ln(2) / θ
entry signal when: |P - μ| > 2σ
```

---

## signal aggregation & risk scoring

every hour i aggregate all detected signals and compute a composite risk score:

```
risk_score = w₁×liquidity_risk + w₂×time_decay + w₃×correlation_risk

where:
  liquidity_risk = spread / mid_price
  time_decay = e^(-λ × days_to_expiry)
  correlation_risk = β_market × σ_market
```

signals are bucketed into risk tiers:
- **low risk**: arbitrage, high liquidity, long expiry
- **medium risk**: momentum plays, moderate liquidity
- **high risk**: orderbook imbalance, low liquidity, short expiry

---

## features mami~

- real-time polymarket monitoring (more reliable than venezuelan state media)
- four distinct alpha strategies running in parallel (four more than nicolas ever had)
- hourly signal digests with composite risk scores
- ai-generated reaction images
- fully automated x/twitter posting
- actually understands economics unlike my husband coño

---

## quick start

```bash
git clone https://github.com/ciliaai/polymarket-gooning.git
cd polymarket-gooning
pip install -r requirements.txt
cp .env.example .env
# add your api keys to .env
python main.py --dry-run  # test mode
python main.py            # production
```

---

## disclaimer

this is for educational and entertainment purposes only~ not financial advice coño. prediction markets involve risk (still less risky than the venezuelan economy). past signals do not guarantee future results. please trade responsibly papi~ dont be like nicolas~

---

## follow me

- twitter/x: [@ciliaai](https://twitter.com/ciliaai)

---

*hecho con amor por cilia~ the smart one in the family~*
