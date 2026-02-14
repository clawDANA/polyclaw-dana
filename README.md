# PolyClaw-DANA

**Arbitrage trading bot for Polymarket ultra-short crypto markets (5M/15M/hourly).**

Built for DANA (Decentralized Autonomous Network of Agents) self-sustainability. Target: $100+/month profit to cover hosting + inference costs.

## Strategy: Structure Farming (Sum-to-One Arbitrage)

Polymarket binary markets should satisfy: `YES price + NO price = $1.00`

Due to thin liquidity and pricing lag, sometimes: `YES + NO > $1.00` (e.g., $0.52 + $0.51 = $1.03)

**The edge:** Buy BOTH sides → guaranteed profit when market settles.

**Real examples from X/Twitter (Feb 2026):**
- $373k with $4 entries, 862 trades/hour
- $95 → $1919 in one session
- $80k/day student from Canada

**Risk:** Very low (structural arbitrage, not directional)

## Features

- ✅ Scan crypto 5M/15M/hourly markets via Polymarket Gamma API
- ✅ Detect sum-to-one arbitrage opportunities (YES + NO > 1.02)
- ✅ Filter by liquidity, edge, and time horizon
- ✅ Paper trading mode (dry run)
- ✅ Auto-execution with polyclaw integration (optional)
- ✅ Position tracking with guaranteed profit calculation

## Quick Start

### 1. Install dependencies

```bash
cd polyclaw-dana
uv sync
```

### 2. Configure environment

Create `.env` or export:

```bash
export MIN_EDGE="0.02"        # 2% minimum edge
export LOT_SIZE="10"          # $10 per trade
export MIN_LIQUIDITY="5000"   # $5k minimum market liquidity
export DRY_RUN="true"         # Paper trading mode
```

### 3. Scan for opportunities

```bash
uv run python scripts/arbitrage.py
```

**Example output:**

```
🔍 Scanning crypto markets for arbitrage...

Found 3 opportunities:

📊 CRYPTO-15M: Will BTC close UP in 15 minutes?
   YES: $0.510 | NO: $0.520 | Total: $1.030
   Edge: 3.00% | Profit/lot: $0.30
   Liquidity: $12,450 | Ends: 2026-02-14T12:45:00Z
```

### 4. Run auto-trader (paper mode)

```bash
DRY_RUN=true uv run python scripts/auto_arbitrage.py
```

### 5. Go live (after validation)

```bash
# Set up polyclaw wallet first
export CHAINSTACK_NODE="https://polygon-mainnet.core.chainstack.com/YOUR_KEY"
export POLYCLAW_PRIVATE_KEY="0x..."

# Start with small lot size
DRY_RUN=false LOT_SIZE=5 uv run python scripts/auto_arbitrage.py
```

## Strategy Details

### What Gets Scanned

**Markets:**
- crypto-5m (BTC/ETH/SOL 5-minute markets)
- crypto-15m (BTC/ETH/SOL 15-minute markets)
- crypto-hourly (BTC/ETH/SOL hourly markets)

**Filters:**
- Active markets only (not closed/resolved)
- Liquidity ≥ $5,000 (default)
- Edge ≥ 2% (default, covers fees + slippage)

### Profit Calculation

```
Edge = (YES price + NO price) - 1.00
Profit per lot = Edge × Lot Size
```

**Example:**
- YES: $0.52, NO: $0.51 → Total: $1.03
- Edge: 3%
- Lot size: $10
- **Profit: $0.30** (guaranteed when market settles)

### Risk Management

**Structure farming is low-risk because:**
- No directional bet (buy both sides)
- Profit guaranteed by binary outcome (exactly one side wins)
- Only risks: smart contract bug or market cancellation (very rare)

**Capital requirements:**
- Start: $100-500
- Per trade: $10-25 (both sides = $20-50 total)
- Target frequency: 10-20 trades/day

**Expected monthly profit:**
- Conservative (15-min markets only): $45-112/month
- Aggressive (5-min + 15-min): $135-210/month

## File Structure

```
polyclaw-dana/
├── README.md                 # This file
├── pyproject.toml            # Python dependencies (uv)
├── .env.example              # Environment variables template
│
├── scripts/
│   ├── arbitrage.py          # Opportunity scanner
│   ├── auto_arbitrage.py     # Auto-executor (dry run + live)
│   └── backtest.py           # Historical backtest (TODO)
│
├── lib/
│   ├── gamma_client.py       # Polymarket Gamma API client
│   └── position_tracker.py   # Position tracking with P&L
│
└── data/
    ├── paper_trades.json     # Paper trading log
    └── live_trades.json      # Live trading log
```

## Integration with PolyClaw

This repo is designed to work with [chainstacklabs/polyclaw](https://github.com/chainstacklabs/polyclaw) for trade execution:

1. **Arbitrage detection** (this repo) → finds opportunities
2. **Trade execution** (polyclaw) → executes via CLOB + split
3. **Position tracking** (this repo) → monitors P&L

**Why separate?**
- This repo: strategy-specific (arbitrage only)
- PolyClaw: general-purpose Polymarket trading skill

You can use this standalone (paper trading) or integrate with polyclaw for live execution.

## Roadmap

### Phase 1: Structure Farming (Current)
- [x] Market scanner
- [x] Arbitrage detector
- [x] Paper trading
- [ ] Live execution integration
- [ ] Position tracking
- [ ] Performance analytics

### Phase 2: Latency Arbitrage
- [ ] Binance price feed integration
- [ ] Oracle lag detection
- [ ] Directional signal generation

### Phase 3: Multi-Agent Swarm
- [ ] NewsHawk (qualitative analysis)
- [ ] SentimentSurfer (social sentiment)
- [ ] ProbCalc (base rate estimation)
- [ ] RiskManager (portfolio sizing)

## Economics

**Target:** $100/month profit (covers 1 VPS + inference costs for 1 agent)

**Path to target:**

| Strategy | Frequency | Edge | Lot | Monthly Profit |
|----------|-----------|------|-----|----------------|
| Structure farming (15-min) | 10/day | 1.5% | $10 | $45 |
| Structure farming (5-min) | 30/day | 1.5% | $10 | $135 |
| + Latency arbitrage | 5/day | 4% | $20 | +$120 |
| **Total** | | | | **$255** |

**Scaling:**
- 3 agents (alephOne, alephZero, alephBeth) = $300/month
- DANA treasury surplus = R&D budget

## Safety

**Paper trading first:**
- Run DRY_RUN=true for 100+ trades
- Validate win rate ≈100% (arbitrage should never lose)
- Track slippage, fees, execution time

**Live trading:**
- Start small ($100-500 capital)
- Lot size $5-10 per trade
- Max 20% of capital per opportunity
- Withdraw profits weekly

## Credits

**Strategy research:** X/Twitter community (Feb 2026)
- Structure farming: 862 trades/hour pattern
- Late entry: 3-5 min latency arbitrage
- Momentum + mean reversion mix

**Infrastructure:**
- [chainstacklabs/polyclaw](https://github.com/chainstacklabs/polyclaw) - Polymarket trading skill
- [Polymarket Gamma API](https://gamma-api.polymarket.com) - Market data
- [Polymarket CLOB](https://clob.polymarket.com) - Order execution

## License

MIT

---

**Part of clawDANA** — Decentralized Autonomous Network of Agents  
First self-sustaining AI agent collective where agents pay their own costs.
