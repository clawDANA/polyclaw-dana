"""Polymarket Gamma API client for crypto market scanning."""

import json
from typing import Optional
import httpx


GAMMA_API_BASE = "https://gamma-api.polymarket.com"


class GammaClient:
    """HTTP client for Polymarket Gamma API."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def get_crypto_markets(self, slugs: list[str] = None) -> list[dict]:
        """Get crypto ultra-short markets by event slug.
        
        Args:
            slugs: List of event slugs (default: ['crypto-5m', 'crypto-15m', 'crypto-hourly'])
        
        Returns:
            List of market dictionaries with parsed data
        """
        if slugs is None:
            slugs = ['crypto-5m', 'crypto-15m', 'crypto-hourly']
        
        all_markets = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as http:
            for slug in slugs:
                try:
                    # Fetch event by slug
                    resp = await http.get(f"{GAMMA_API_BASE}/events/{slug}")
                    if resp.status_code != 200:
                        print(f"Warning: {slug} returned {resp.status_code}")
                        continue
                    
                    event = resp.json()
                    markets = event.get('markets', [])
                    
                    for market in markets:
                        parsed = self._parse_market(market, event, slug)
                        if parsed:
                            all_markets.append(parsed)
                
                except Exception as e:
                    print(f"Error fetching {slug}: {e}")
                    continue
        
        return all_markets

    def _parse_market(self, market: dict, event: dict, slug: str) -> Optional[dict]:
        """Parse market JSON into structured dict.
        
        Args:
            market: Market data from API
            event: Parent event data
            slug: Event slug (crypto-5m, crypto-15m, etc)
        
        Returns:
            Parsed market dict or None if invalid
        """
        try:
            # Skip closed/resolved markets
            if market.get('closed') or market.get('resolved') or not market.get('active'):
                return None
            
            # Parse prices
            prices_str = market.get('outcomePrices', '[0.5, 0.5]')
            prices = json.loads(prices_str) if isinstance(prices_str, str) else prices_str
            
            yes_price = float(prices[0]) if len(prices) > 0 else 0.5
            no_price = float(prices[1]) if len(prices) > 1 else (1.0 - yes_price)
            
            # Parse token IDs (for CLOB trading)
            token_ids_str = market.get('clobTokenIds', '[]')
            token_ids = json.loads(token_ids_str) if isinstance(token_ids_str, str) else token_ids_str
            
            return {
                'event_slug': slug,
                'event_title': event.get('title', ''),
                'event_id': event.get('id', ''),
                'market_id': market.get('id', ''),
                'question': market.get('question', ''),
                'slug': market.get('slug', ''),
                'yes_price': yes_price,
                'no_price': no_price,
                'yes_token_id': token_ids[0] if len(token_ids) > 0 else None,
                'no_token_id': token_ids[1] if len(token_ids) > 1 else None,
                'volume_24h': float(market.get('volume24hr', 0) or 0),
                'liquidity': float(market.get('liquidity', 0) or 0),
                'end_date': market.get('endDate'),
                'active': market.get('active', False),
                'closed': market.get('closed', False),
                'resolved': market.get('resolved', False),
                'url': f"https://polymarket.com/event/{event.get('slug', '')}/{market.get('slug', '')}"
            }
        
        except Exception as e:
            print(f"Error parsing market: {e}")
            return None


# Sync wrapper for convenience
def fetch_crypto_markets(slugs: list[str] = None) -> list[dict]:
    """Synchronous wrapper for get_crypto_markets.
    
    Args:
        slugs: List of event slugs
    
    Returns:
        List of market dictionaries
    """
    import asyncio
    client = GammaClient()
    return asyncio.run(client.get_crypto_markets(slugs))
