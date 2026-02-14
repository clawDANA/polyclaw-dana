#!/usr/bin/env python3
"""Real-time arbitrage scanner for active ultra-short crypto markets.

Combines timestamp-based market discovery with Gamma API price fetching
to find structure farming opportunities.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

from timestamp_markets import get_current_markets, generate_market_urls
from gamma_client import GammaClient


async def scan_active_markets(intervals: list[str] = None, min_edge: float = 0.015):
    """Scan currently active markets for arbitrage opportunities.
    
    Args:
        intervals: Market intervals to scan ('5m', '15m', 'hourly')
        min_edge: Minimum edge threshold (default 1.5%)
    
    Returns:
        List of markets with arbitrage opportunities
    """
    if intervals is None:
        intervals = ['5m', '15m']
    
    # Get currently active markets
    active_markets = get_current_markets(intervals)
    
    if not active_markets:
        print("No active markets right now")
        return []
    
    print(f"📊 Scanning {len(active_markets)} active market(s)...\n")
    
    # Fetch prices via API
    client = GammaClient()
    slugs = [m['slug'] for m in active_markets]
    
    market_data = await client.get_markets_by_slugs(slugs)
    
    # Filter for arbitrage opportunities
    opportunities = []
    
    for market in market_data:
        if market and market['has_arbitrage']:
            opportunities.append(market)
    
    return market_data, opportunities


async def main():
    """Main entry point."""
    print("🔍 Ultra-Short Market Scanner")
    print(f"⏰ Current time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*70 + "\n")
    
    # Scan active markets
    all_markets, arbitrage_opps = await scan_active_markets(['5m', '15m'])
    
    if not all_markets:
        print("❌ No markets currently active")
        print("\nNext markets open soon:")
        upcoming = generate_market_urls(['5m', '15m'], look_ahead_hours=1)
        for m in upcoming[:3]:
            print(f"  {m['interval'].upper()}: {m['close_time']} (in {m['minutes_until_close']} min)")
        return
    
    # Display all scanned markets
    print("Scanned Markets:\n")
    for market in all_markets:
        interval = market['slug'].split('-')[2]  # Extract interval from slug
        time_remaining = "?" 
        
        print(f"{interval.upper()} | {market['question'][:60]}...")
        print(f"      YES: ${market['yes_price']:.4f} | NO: ${market['no_price']:.4f} | Total: ${market['total']:.4f}")
        
        if market['has_arbitrage']:
            print(f"      💰 ARBITRAGE: {market['edge_pct']:.2f}% edge | Profit/lot: ${market['edge']*10:.3f} ($10 lot)")
        else:
            print(f"      Edge: {market['edge_pct']:.2f}%")
        
        print(f"      Liquidity: ${market['liquidity']:,.0f} | Active: {market['active']}")
        print(f"      {market['url']}")
        print()
    
    # Summary
    print("="*70)
    if arbitrage_opps:
        print(f"\n🎯 FOUND {len(arbitrage_opps)} ARBITRAGE OPPORTUNITY(IES)!")
        
        for opp in arbitrage_opps:
            print(f"\n  Market: {opp['question']}")
            print(f"  Edge: {opp['edge_pct']:.2f}%")
            print(f"  Strategy: Buy both YES (${opp['yes_price']:.4f}) + NO (${opp['no_price']:.4f})")
            print(f"  Guaranteed profit: ${opp['edge']*10:.3f} per $10 lot")
            print(f"  URL: {opp['url']}")
    else:
        print("\n✓ All markets efficiently priced (no arbitrage > 1.5%)")
        print("\nKeep scanning - opportunities appear during:")
        print("  - Thin liquidity periods")
        print("  - Rapid BTC price movements")
        print("  - Market open/close transitions")


if __name__ == "__main__":
    asyncio.run(main())
