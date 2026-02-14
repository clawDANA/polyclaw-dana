#!/usr/bin/env python3
"""Structure farming detector for ultra-short crypto markets.

Scans Polymarket 5M/15M/hourly markets for sum-to-one arbitrage opportunities.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from gamma_client import GammaClient


async def scan_arbitrage_opportunities(
    min_edge: float = 0.02,
    min_liquidity: float = 5000.0,
    slugs: list[str] = None
) -> list[dict]:
    """Scan crypto markets for sum-to-one arbitrage.
    
    Binary markets should satisfy: YES + NO = $1.00
    When YES + NO > $1.00, we can buy both sides for guaranteed profit.
    
    Args:
        min_edge: Minimum edge required (default 2% = 0.02)
        min_liquidity: Minimum market liquidity (default $5,000)
        slugs: Event slugs to scan (default: 5m, 15m, hourly)
    
    Returns:
        List of arbitrage opportunities sorted by edge (best first)
    """
    client = GammaClient()
    
    print(f"🔍 Scanning crypto markets...")
    print(f"   Min edge: {min_edge*100:.1f}%")
    print(f"   Min liquidity: ${min_liquidity:,.0f}")
    print()
    
    # Fetch all crypto markets
    markets = await client.get_crypto_markets(slugs)
    print(f"   Fetched {len(markets)} active markets\n")
    
    opportunities = []
    
    for market in markets:
        # Skip if insufficient liquidity
        if market['liquidity'] < min_liquidity:
            continue
        
        yes_price = market['yes_price']
        no_price = market['no_price']
        total = yes_price + no_price
        edge = total - 1.0
        
        # Check if edge meets threshold
        if edge >= min_edge:
            opportunities.append({
                **market,
                'total': total,
                'edge': edge,
                'edge_pct': edge * 100,
                'profit_per_10': edge * 10,  # Profit on $10 lot size
                'profit_per_100': edge * 100,
            })
    
    # Sort by edge (best first)
    opportunities.sort(key=lambda x: x['edge'], reverse=True)
    
    return opportunities


def print_opportunities(opps: list[dict], limit: int = None):
    """Pretty-print arbitrage opportunities.
    
    Args:
        opps: List of opportunity dicts
        limit: Max number to print (None = all)
    """
    if not opps:
        print("❌ No arbitrage opportunities found above threshold.\n")
        return
    
    print(f"✅ Found {len(opps)} opportunities:\n")
    
    display_opps = opps[:limit] if limit else opps
    
    for i, opp in enumerate(display_opps, 1):
        print(f"#{i} | {opp['event_slug'].upper()}")
        print(f"    {opp['question'][:70]}...")
        print(f"    YES: ${opp['yes_price']:.4f} | NO: ${opp['no_price']:.4f} | Total: ${opp['total']:.4f}")
        print(f"    💰 Edge: {opp['edge_pct']:.2f}% | Profit/lot: ${opp['profit_per_10']:.3f} ($10 lot)")
        print(f"    📊 Liquidity: ${opp['liquidity']:,.0f} | Volume 24h: ${opp['volume_24h']:,.0f}")
        print(f"    ⏰ Ends: {opp['end_date']}")
        print(f"    🔗 {opp['url']}")
        print()
    
    if limit and len(opps) > limit:
        print(f"... and {len(opps) - limit} more opportunities\n")


async def main():
    """Main entry point."""
    # Load config from env
    min_edge = float(os.getenv('MIN_EDGE', '0.02'))
    min_liquidity = float(os.getenv('MIN_LIQUIDITY', '5000'))
    slugs_str = os.getenv('MARKET_SLUGS', 'crypto-5m,crypto-15m,crypto-hourly')
    slugs = [s.strip() for s in slugs_str.split(',')]
    
    # Scan for opportunities
    opps = await scan_arbitrage_opportunities(
        min_edge=min_edge,
        min_liquidity=min_liquidity,
        slugs=slugs
    )
    
    # Print results
    print_opportunities(opps, limit=10)
    
    # Save to JSON
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "arbitrage_scan.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.utcnow().isoformat(),
            'config': {
                'min_edge': min_edge,
                'min_liquidity': min_liquidity,
                'slugs': slugs
            },
            'opportunities': opps
        }, f, indent=2)
    
    print(f"💾 Saved {len(opps)} opportunities to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
