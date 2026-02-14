"""Timestamp-based market URL generator for Polymarket ultra-short crypto markets.

These markets use predictable timestamp-based URLs:
- btc-updown-5m-{close_timestamp}  — 5-minute BTC markets
- btc-updown-15m-{close_timestamp} — 15-minute BTC markets  
- btc-updown-hourly-{close_timestamp} — Hourly BTC markets (TBD)

Timestamp = market close time in Unix epoch seconds (UTC)
"""

from datetime import datetime, timedelta, timezone
from typing import List, Dict


def generate_market_urls(
    intervals: List[str] = None,
    look_ahead_hours: int = 2
) -> List[Dict[str, any]]:
    """Generate upcoming market URLs based on timestamp pattern.
    
    Args:
        intervals: List of intervals to generate ('5m', '15m', 'hourly')
        look_ahead_hours: How many hours ahead to generate (default 2)
    
    Returns:
        List of dicts with market metadata
    """
    if intervals is None:
        intervals = ['5m', '15m']
    
    markets = []
    now = datetime.now(timezone.utc)
    
    for interval in intervals:
        # Determine cycle duration
        if interval == '5m':
            cycle_minutes = 5
            cycle_seconds = 300
        elif interval == '15m':
            cycle_minutes = 15
            cycle_seconds = 900
        elif interval == 'hourly':
            cycle_minutes = 60
            cycle_seconds = 3600
        else:
            continue
        
        # Round to next market close time
        # Markets close at round intervals: XX:00, XX:05, XX:10, ... for 5m
        minutes_to_next = cycle_minutes - (now.minute % cycle_minutes)
        next_close = now + timedelta(
            minutes=minutes_to_next,
            seconds=-now.second,
            microseconds=-now.microsecond
        )
        
        # Generate markets for next N hours
        end_time = now + timedelta(hours=look_ahead_hours)
        
        current_close = next_close
        while current_close <= end_time:
            close_timestamp = int(current_close.timestamp())
            
            # Calculate open time (close_time - interval)
            open_time = current_close - timedelta(seconds=cycle_seconds)
            
            markets.append({
                'interval': interval,
                'open_time': open_time.isoformat(),
                'close_time': current_close.isoformat(),
                'close_timestamp': close_timestamp,
                'url': f"https://polymarket.com/event/btc-updown-{interval}-{close_timestamp}",
                'slug': f"btc-updown-{interval}-{close_timestamp}",
                'minutes_until_close': int((current_close - now).total_seconds() / 60)
            })
            
            # Next market
            current_close += timedelta(seconds=cycle_seconds)
    
    return markets


def get_current_markets(intervals: List[str] = None) -> List[Dict[str, any]]:
    """Get currently active markets (open but not yet closed).
    
    Args:
        intervals: List of intervals ('5m', '15m', 'hourly')
    
    Returns:
        List of active market dicts
    """
    all_markets = generate_market_urls(intervals=intervals, look_ahead_hours=1)
    now = datetime.now(timezone.utc)
    
    # Filter for markets that are currently open
    active = []
    for market in all_markets:
        close_time = datetime.fromisoformat(market['close_time'])
        open_time = datetime.fromisoformat(market['open_time'])
        
        if open_time <= now < close_time:
            active.append(market)
    
    return active


def get_next_market(interval: str = '15m') -> Dict[str, any]:
    """Get the next upcoming market for an interval.
    
    Args:
        interval: Market interval ('5m', '15m', 'hourly')
    
    Returns:
        Market dict
    """
    markets = generate_market_urls(intervals=[interval], look_ahead_hours=1)
    return markets[0] if markets else None


if __name__ == "__main__":
    # Test the generator
    print("Current time:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    print("\n" + "="*70)
    
    print("\n📊 Currently ACTIVE markets:")
    active = get_current_markets(['5m', '15m'])
    for m in active:
        print(f"\n{m['interval'].upper()} market:")
        print(f"  Open:  {m['open_time']}")
        print(f"  Close: {m['close_time']} (in {m['minutes_until_close']} min)")
        print(f"  URL:   {m['url']}")
    
    print("\n" + "="*70)
    print("\n🔮 Next 10 upcoming markets:")
    upcoming = generate_market_urls(['5m', '15m'], look_ahead_hours=1)
    for i, m in enumerate(upcoming[:10], 1):
        status = "🟢 ACTIVE" if m['minutes_until_close'] <= 15 and m['minutes_until_close'] > 0 else "⏳ UPCOMING"
        print(f"{i}. {m['interval'].upper()} - closes {m['close_time']} ({status})")
        print(f"   {m['url']}")
