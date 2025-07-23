import datetime as dt
import time
import requests
from lxml import html
from decimal import Decimal
from typing import Optional, Dict, Any

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging

from .models import PriceSnapshot, APICallLog

logger = logging.getLogger('price')


class SberPriceService:
    """Service class for handling Sber price calculations and data fetching"""
    
    def __init__(self):
        self.stocks_quantity = settings.SBER_STOCKS_QUANTITY
        self.cbr_base_url = settings.CBR_BASE_URL
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0)'
                          'Gecko/20100101 Firefox/45.0')
        }
        
        # MOEX API URLs
        self.moex_urls = {
            'current': 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/SBER.json?iss.meta=off&iss.only=marketdata&marketdata.columns=LAST',
            'prev': 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/SBER.json?iss.meta=off&iss.only=securities&securities.columns=PREVPRICE',
            'market': 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/SBER.json?iss.meta=off&iss.only=marketdata&marketdata.columns=MARKETPRICE'
        }
    
    def _make_api_call(self, url: str, api_name: str, timeout: int = 5) -> Optional[requests.Response]:
        """Make API call with logging and error handling"""
        start_time = time.time()
        
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            
            # Log successful calls
            response_time = int((time.time() - start_time) * 1000)
            APICallLog.objects.create(
                api_name=api_name,
                url=url,
                status_code=response.status_code,
                response_time_ms=response_time,
                success=True
            )
            
            logger.info(f"API call to {api_name} successful: {response.status_code} ({response_time}ms)")
            return response
            
        except requests.exceptions.RequestException as e:
            response_time = int((time.time() - start_time) * 1000)
            status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            
            APICallLog.objects.create(
                api_name=api_name,
                url=url,
                status_code=status_code,
                response_time_ms=response_time,
                success=False,
                error_message=str(e)[:500]  # Limit error message length
            )
            
            logger.error(f"API call to {api_name} failed: {e}")
            return None
    
    def get_used_month(self) -> str:
        """Get the month to use for CBR data based on current date"""
        # Используем московское время из Django timezone
        now = timezone.localtime(timezone.now())
        if now.day > 25:
            return now.strftime('%m')
        return (now - dt.timedelta(days=27)).strftime('%m')
    
    def get_cbr_url(self, used_month: str) -> str:
        """Generate CBR URL for the given month"""
        return f'{self.cbr_base_url}?regnum=1481&dt=2025-{used_month}-01'
    
    def parse_own_capital(self) -> Optional[int]:
        """Parse own capital from CBR website with caching"""
        cache_key = f'own_capital_{self.get_used_month()}'
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            logger.info(f'Using cached own capital: {cached_value}')
            return cached_value
        
        try:
            url = self.get_cbr_url(self.get_used_month())
            response = self._make_api_call(url, 'cbr')
            
            if not response:
                return None
            
            tree = html.fromstring(response.content)
            
            # Try multiple XPath expressions for robustness
            xpath_expressions = [
                '/html/body/main/div/div/div/div[3]/div[2]/table/tr[2]/td[3]/text()',
                '//table//tr[2]/td[3]/text()',
                '//td[contains(@class, "capital")]/text()',  # If they add CSS classes
            ]
            
            parsed_string = None
            for xpath in xpath_expressions:
                try:
                    result = tree.xpath(xpath)
                    if result:
                        parsed_string = result[0]
                        break
                except Exception as e:
                    logger.warning(f"XPath {xpath} failed: {e}")
                    continue
            
            if not parsed_string:
                logger.error("Could not parse own capital from CBR website")
                return None
            
            own_capital = int(parsed_string.replace(' ', '')) * 1000
            
            # Cache for 1 hour
            cache.set(cache_key, own_capital, 3600)
            logger.info(f'Parsed and cached own capital: {own_capital}')
            
            return own_capital
            
        except Exception as e:
            logger.error(f"Error parsing own capital: {e}")
            return None
    
    def get_moex_price(self) -> Optional[float]:
        """Get MOEX price with fallback options and caching"""
        cache_key = 'moex_price'
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            logger.info(f'Using cached MOEX price: {cached_value}')
            return cached_value
        
        # Try different price sources in order of preference
        for price_type, url in self.moex_urls.items():
            try:
                response = self._make_api_call(url, f'moex_{price_type}')
                if not response:
                    continue
                
                data = response.json()
                
                if price_type == 'current':
                    price = data['marketdata']['data'][0][0]
                elif price_type == 'prev':
                    price = data['securities']['data'][0][0]
                else:  # market
                    price = data['marketdata']['data'][0][0]
                
                if price is not None:
                    # Cache for 1 minute during trading hours, 5 minutes otherwise
                    cache_timeout = 60 if self._is_trading_hours() else 300
                    cache.set(cache_key, price, cache_timeout)
                    logger.info(f'Got MOEX price from {price_type}: {price}')
                    return price
                    
            except (KeyError, IndexError, ValueError) as e:
                logger.warning(f"Failed to parse {price_type} price: {e}")
                continue
        
        logger.error("Could not get MOEX price from any source")
        return None
    
    def _is_trading_hours(self) -> bool:
        """Check if current time is during trading hours (rough approximation)"""
        # Используем московское время из Django timezone
        now = timezone.localtime(timezone.now())
        # Moscow Exchange trading hours: roughly 10:00-18:45 Moscow time, Mon-Fri
        return (now.weekday() < 5 and 
                10 <= now.hour < 19)
    
    def get_fair_price(self) -> Optional[float]:
        """Calculate fair price based on own capital"""
        own_capital = self.parse_own_capital()
        if own_capital is None:
            return None
        
        fair_price = round(own_capital / self.stocks_quantity, 2)
        logger.info(f'Calculated fair price: {fair_price}')
        return fair_price
    
    def get_pb_ratio(self) -> Optional[float]:
        """Calculate P/B ratio"""
        moex_price = self.get_moex_price()
        fair_price = self.get_fair_price()
        
        if moex_price is None or fair_price is None:
            return None
        
        pb_ratio = round(moex_price / fair_price, 2)
        logger.info(f'Calculated P/B ratio: {pb_ratio}')
        return pb_ratio
    
    def get_price_score(self) -> str:
        """Get price evaluation based on P/B ratio"""
        pb_ratio = self.get_pb_ratio()
        
        if pb_ratio is None:
            return 'неизвестно'
        
        if pb_ratio < 1:
            return 'дешево'
        elif 1 <= pb_ratio <= 1.2:
            return 'справедливо'
        elif 1.2 < pb_ratio < 1.4:
            return 'чуть дорого'
        return 'дорого'
    
    def get_current_data(self) -> Dict[str, Any]:
        """Get all current price data with optimized caching"""
        # Check if we have cached complete data
        cache_key = 'current_data_complete'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            logger.info('Using cached complete current data')
            return cached_data
        
        # Get data once and calculate everything from it
        moex_price = self.get_moex_price()
        fair_price = self.get_fair_price()
        
        # Calculate P/B ratio directly without additional method calls
        pb_ratio = None
        if moex_price is not None and fair_price is not None:
            pb_ratio = round(moex_price / fair_price, 2)
        
        # Calculate price score directly
        price_score = 'неизвестно'
        if pb_ratio is not None:
            if pb_ratio < 1:
                price_score = 'дешево'
            elif 1 <= pb_ratio <= 1.2:
                price_score = 'справедливо'
            elif 1.2 < pb_ratio < 1.4:
                price_score = 'чуть дорого'
            else:
                price_score = 'дорого'
        
        data = {
            'moex_price': moex_price,
            'fair_price': fair_price,
            'fair_price_20_percent': round(fair_price * 1.2, 2) if fair_price else None,
            'pb_ratio': pb_ratio,
            'price_score': price_score,
            'timestamp': timezone.now()
        }
        
        # Cache complete data for 30 seconds to avoid repeated calculations
        cache.set(cache_key, data, 30)
        logger.info('Cached complete current data')
        
        return data
    
    def save_snapshot(self) -> Optional[PriceSnapshot]:
        """Save current data as a snapshot"""
        try:
            data = self.get_current_data()
            own_capital = self.parse_own_capital()
            
            snapshot = PriceSnapshot.objects.create(
                moex_price=Decimal(str(data['moex_price'])) if data['moex_price'] else None,
                fair_price=Decimal(str(data['fair_price'])) if data['fair_price'] else None,
                pb_ratio=Decimal(str(data['pb_ratio'])) if data['pb_ratio'] else None,
                own_capital=own_capital,
                price_score=data['price_score']
            )
            
            logger.info(f'Saved price snapshot: {snapshot.id}')
            return snapshot
            
        except Exception as e:
            logger.error(f'Failed to save snapshot: {e}')
            return None
    
    def get_historical_data(self, days: int = 30) -> list:
        """Get historical snapshots for the last N days"""
        cutoff_date = timezone.now() - dt.timedelta(days=days)
        return PriceSnapshot.objects.filter(timestamp__gte=cutoff_date)


# Global service instance
sber_service = SberPriceService()