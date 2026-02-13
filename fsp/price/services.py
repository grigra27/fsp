import datetime as dt
import time
import requests
from lxml import html
from typing import Optional, Dict, Any

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging

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
        
        # MOEX API URLs (using HTTP instead of HTTPS due to hosting restrictions)
        self.moex_urls = {
            'current': 'http://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/SBER.json?iss.meta=off&iss.only=marketdata&marketdata.columns=LAST',
            'prev': 'http://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/SBER.json?iss.meta=off&iss.only=securities&securities.columns=PREVPRICE',
            'market': 'http://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/SBER.json?iss.meta=off&iss.only=marketdata&marketdata.columns=MARKETPRICE'
        }
    
    def _make_api_call(self, url: str, api_name: str, timeout: int = 20, retries: int = 3) -> Optional[requests.Response]:
        """Make API call with error handling and retry logic"""
        for attempt in range(retries):
            start_time = time.time()
            
            try:
                response = requests.get(url, headers=self.headers, timeout=timeout)
                response.raise_for_status()
                
                response_time = int((time.time() - start_time) * 1000)
                logger.info(f"API call to {api_name} successful: {response.status_code} ({response_time}ms) [attempt {attempt + 1}/{retries}]")
                return response
                
            except requests.exceptions.RequestException as e:
                response_time = int((time.time() - start_time) * 1000)
                if attempt < retries - 1:
                    logger.warning(f"API call to {api_name} failed (attempt {attempt + 1}/{retries}): {e}, retrying...")
                    time.sleep(1)  # Wait 1 second before retry
                else:
                    logger.error(f"API call to {api_name} failed after {retries} attempts: {e}")
        
        return None
    
    def get_used_month(self) -> str:
        """Get the month to use for CBR data based on current date"""
        now = timezone.localtime(timezone.now())
        if now.day > 25:
            return now.strftime('%m')
        return (now - dt.timedelta(days=27)).strftime('%m')
    
    def get_cbr_url(self, used_month: str) -> str:
        """Generate CBR URL for the given month"""
        now = timezone.localtime(timezone.now())
        used_month_int = int(used_month)

        # If we are before the 25th and requested month is greater than current
        # month, it belongs to the previous year (e.g. January -> December).
        year = now.year
        if now.day <= 25 and used_month_int > now.month:
            year -= 1

        return f'{self.cbr_base_url}?regnum=1481&dt={year}-{used_month}-01'
    
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
                '//td[contains(@class, "capital")]/text()',
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
                response = self._make_api_call(url, f'moex_{price_type}', timeout=20, retries=2)
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
                    # Cache for 5 minutes during trading hours, 30 minutes otherwise
                    cache_timeout = 300 if self._is_trading_hours() else 1800
                    cache.set(cache_key, price, cache_timeout)
                    # Also save as fallback with longer TTL (7 days)
                    cache.set(f'{cache_key}_fallback', price, 604800)
                    logger.info(f'Got MOEX price from {price_type}: {price}')
                    return price
                    
            except (KeyError, IndexError, ValueError) as e:
                logger.warning(f"Failed to parse {price_type} price: {e}")
                continue
        
        # If all sources failed, try to use fallback cache
        fallback_value = cache.get(f'{cache_key}_fallback')
        if fallback_value is not None:
            logger.warning(f'Using fallback MOEX price (may be stale): {fallback_value}')
            return fallback_value
        
        logger.error("Could not get MOEX price from any source")
        return None
    
    def _is_trading_hours(self) -> bool:
        """Check if current time is during trading hours"""
        now = timezone.localtime(timezone.now())
        return (now.weekday() < 5 and 10 <= now.hour < 19)
    
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
        """Get all current price data with caching"""
        cache_key = 'current_data_complete'
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            logger.info('Using cached complete current data')
            return cached_data
        
        moex_price = self.get_moex_price()
        fair_price = self.get_fair_price()
        
        pb_ratio = None
        if moex_price is not None and fair_price is not None:
            pb_ratio = round(moex_price / fair_price, 2)
        
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
        
        # Cache for 2 minutes
        cache.set(cache_key, data, 120)
        logger.info('Cached complete current data')
        
        return data


# Global service instance
sber_service = SberPriceService()
