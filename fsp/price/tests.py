import datetime as dt
from unittest import mock

from django.core.cache import cache
from django.test import SimpleTestCase

from price.services import SberPriceService


class SberPriceServiceTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.service = SberPriceService()

    @mock.patch('price.services.timezone.localtime', side_effect=lambda value: value)
    @mock.patch('price.services.timezone.now')
    def test_get_cbr_url_uses_current_year_after_25th(self, mocked_now, _mocked_localtime):
        mocked_now.return_value = dt.datetime(2026, 2, 26, tzinfo=dt.timezone.utc)

        url = self.service.get_cbr_url('02')

        self.assertIn('dt=2026-02-01', url)

    @mock.patch('price.services.timezone.localtime', side_effect=lambda value: value)
    @mock.patch('price.services.timezone.now')
    def test_get_cbr_url_handles_previous_year_boundary(self, mocked_now, _mocked_localtime):
        mocked_now.return_value = dt.datetime(2026, 1, 10, tzinfo=dt.timezone.utc)

        url = self.service.get_cbr_url('12')

        self.assertIn('dt=2025-12-01', url)

    @mock.patch.object(SberPriceService, 'get_pb_ratio')
    def test_get_price_score_ranges(self, mocked_pb_ratio):
        mocked_pb_ratio.return_value = None
        self.assertEqual(self.service.get_price_score(), 'неизвестно')

        mocked_pb_ratio.return_value = 0.99
        self.assertEqual(self.service.get_price_score(), 'дешево')

        mocked_pb_ratio.return_value = 1.0
        self.assertEqual(self.service.get_price_score(), 'справедливо')

        mocked_pb_ratio.return_value = 1.2
        self.assertEqual(self.service.get_price_score(), 'справедливо')

        mocked_pb_ratio.return_value = 1.3
        self.assertEqual(self.service.get_price_score(), 'чуть дорого')

        mocked_pb_ratio.return_value = 1.4
        self.assertEqual(self.service.get_price_score(), 'дорого')

    def test_get_moex_price_uses_fallback_cache(self):
        cache.set('moex_price_fallback', 321.45, 60)

        with mock.patch.object(self.service, '_make_api_call', return_value=None):
            result = self.service.get_moex_price()

        self.assertEqual(result, 321.45)

    def test_get_moex_price_parses_current_source(self):
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            'marketdata': {'data': [[300.12]]}
        }

        with mock.patch.object(self.service, '_is_trading_hours', return_value=True):
            with mock.patch.object(self.service, '_make_api_call', return_value=mock_response):
                result = self.service.get_moex_price()

        self.assertEqual(result, 300.12)
        self.assertEqual(cache.get('moex_price'), 300.12)

    @mock.patch.object(SberPriceService, 'get_fair_price', return_value=None)
    @mock.patch.object(SberPriceService, 'get_moex_price', return_value=250.0)
    def test_get_current_data_handles_none_values(self, _mocked_moex, _mocked_fair):
        data = self.service.get_current_data()

        self.assertEqual(data['moex_price'], 250.0)
        self.assertIsNone(data['fair_price'])
        self.assertIsNone(data['fair_price_20_percent'])
        self.assertIsNone(data['pb_ratio'])
        self.assertEqual(data['price_score'], 'неизвестно')
