"""Web scraper to extract YES/NO prices from Polymarket event pages."""

import httpx
import re
import json
from typing import Optional, Dict


def scrape_market_prices(url: str, timeout: float = 15.0) -> Optional[Dict]:
    """Scrape YES/NO prices from Polymarket event page.
    
    Args:
        url: Full URL to event page
        timeout: Request timeout in seconds
    
    Returns:
        Dict with market data, or None if failed
    """
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        
        if response.status_code != 200:
            return None
        
        html = response.text
        
        # Extract title from page
        title_match = re.search(r'<title>([^<]+)</title>', html)
        title = title_match.group(1) if title_match else "Unknown"
        
        # Look for outcomePrices in JSON data
        # Pattern: "outcomePrices":["0.535","0.465"]
        price_match = re.search(r'"outcomePrices"\s*:\s*\[([^\]]+)\]', html)
        
        if not price_match:
            return None
        
        # Extract price values
        price_str = price_match.group(1)
        prices = re.findall(r'(\d+\.\d+)', price_str)
        
        if len(prices) < 2:
            return None
        
        yes_price = float(prices[0])
        no_price = float(prices[1])
        total = yes_price + no_price
        edge = total - 1.0
        
        return {
            'url': url,
            'title': title.split('|')[0].strip() if '|' in title else title,
            'yes_price': yes_price,
            'no_price': no_price,
            'total': total,
            'edge': edge,
            'edge_pct': edge * 100,
            'has_arbitrage': edge > 0.015  # 1.5%+ threshold
        }
    
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


if __name__ == "__main__":
    # Test with current active market
    test_url = "https://polymarket.com/event/btc-updown-15m-1771086600"
    
    print(f"Scraping: {test_url}\n")
    
    data = scrape_market_prices(test_url)
    
    if data:
        print("✅ Successfully extracted market data:\n")
        print(f"Title: {data['title']}")
        print(f"YES price: ${data['yes_price']:.4f}")
        print(f"NO price: ${data['no_price']:.4f}")
        print(f"Total: ${data['total']:.4f}")
        
        if data['has_arbitrage']:
            print(f"\n💰 ARBITRAGE OPPORTUNITY: {data['edge_pct']:.2f}% edge")
            print(f"   Profit on $10 lot: ${data['edge'] * 10:.3f}")
        else:
            print(f"\nEdge: {data['edge_pct']:.2f}% (no arbitrage)")
    else:
        print("❌ Failed to extract market data")
