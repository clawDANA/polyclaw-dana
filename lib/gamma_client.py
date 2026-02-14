"""Polymarket Gamma API client for ultra-short crypto markets."""

import json
from typing import Optional, List
import httpx


GAMMA_API_BASE = "https://gamma-api.polymarket.com"


class GammaClient:
    """HTTP client for Polymarket Gamma API."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    async def get_market_by_slug(self, slug: str) -> Optional[dict]:
        """Get market by slug via Gamma API.
        
        Args:
            slug: Market slug (e.g., 'btc-updown-15m-1771086600')
        
        Returns:
            Market dict or None if not found
        """
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(
                    f"{GAMMA_API_BASE}/markets",
                    params={"slug": slug}
                )
                
                if resp.status_code == 200:
                    markets = resp.json()
                    
                    if markets and len(markets) > 0:
                        return self._parse_market(markets[0])
                
                return None
            
            except Exception as e:
                print(f"Error fetching market {slug}: {e}")
                return None

    async def get_markets_by_slugs(self, slugs: List[str]) -> List[dict]:
        """Get multiple markets by slug.
        
        Args:
            slugs: List of market slugs
        
        Returns:
            List of parsed market dicts
        """
        markets = []
        
        for slug in slugs:
            market = await self.get_market_by_slug(slug)
            if market:
                markets.append(market)
        
        return markets

    def _parse_market(self, data: dict) -> dict:
        """Parse market JSON into structured dict.
        
        Args:
            data: Market data from API
        
        Returns:
            Parsed market dict
        """
        try:
            # Parse prices
            prices_str = data.get('outcomePrices', '[0.5, 0.5]')
            prices = json.loads(prices_str) if isinstance(prices_str, str) else prices_str
            
            yes_price = float(prices[0]) if len(prices) > 0 else 0.5
            no_price = float(prices[1]) if len(prices) > 1 else (1.0 - yes_price)
            
            # Calculate edge
            total = yes_price + no_price
            edge = total - 1.0
            
            # Parse token IDs
            token_ids_str = data.get('clobTokenIds', '[]')
            token_ids = json.loads(token_ids_str) if isinstance(token_ids_str, str) else token_ids_str
            
            return {
                'market_id': data.get('id'),
                'question': data.get('question', ''),
                'slug': data.get('slug', ''),
                'yes_price': yes_price,
                'no_price': no_price,
                'total': total,
                'edge': edge,
                'edge_pct': edge * 100,
                'has_arbitrage': edge > 0.015,  # 1.5% threshold
                'yes_token_id': token_ids[0] if len(token_ids) > 0 else None,
                'no_token_id': token_ids[1] if len(token_ids) > 1 else None,
                'liquidity': float(data.get('liquidity', 0) or 0),
                'volume_24h': float(data.get('volume24hr', 0) or 0),
                'end_date': data.get('endDate'),
                'active': data.get('active', False),
                'closed': data.get('closed', False),
                'url': f"https://polymarket.com/event/{data.get('slug', '')}"
            }
        
        except Exception as e:
            print(f"Error parsing market: {e}")
            return None


# Sync wrappers for convenience
def fetch_market(slug: str) -> Optional[dict]:
    """Synchronous wrapper for get_market_by_slug."""
    import asyncio
    client = GammaClient()
    return asyncio.run(client.get_market_by_slug(slug))


def fetch_markets(slugs: List[str]) -> List[dict]:
    """Synchronous wrapper for get_markets_by_slugs."""
    import asyncio
    client = GammaClient()
    return asyncio.run(client.get_markets_by_slugs(slugs))


if __name__ == "__main__":
    # Test with current active market
    test_slug = "btc-updown-15m-1771086600"
    
    print(f"Testing Gamma API with slug: {test_slug}\n")
    
    market = fetch_market(test_slug)
    
    if market:
        print("✅ Successfully fetched via API:\n")
        print(f"Question: {market['question']}")
        print(f"YES: ${market['yes_price']:.4f} | NO: ${market['no_price']:.4f}")
        print(f"Total: ${market['total']:.4f}")
        
        if market['has_arbitrage']:
            print(f"\n💰 ARBITRAGE: {market['edge_pct']:.2f}% edge")
        else:
            print(f"\nEdge: {market['edge_pct']:.2f}%")
        
        print(f"\nLiquidity: ${market['liquidity']:,.0f}")
        print(f"Active: {market['active']}")
    else:
        print("❌ Failed to fetch market")
