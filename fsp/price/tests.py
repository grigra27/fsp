import datetime as dt
import os
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


    @mock.patch.dict(os.environ, {'MOEX_BASE_URLS': 'https://a.example,http://b.example'}, clear=False)
    def test_get_moex_base_urls_from_env(self):
        service = SberPriceService()

        self.assertEqual(service.moex_base_urls, ['https://a.example', 'http://b.example'])

    def test_get_moex_price_tries_next_base_url_after_failure(self):
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            'marketdata': {'data': [[301.11]]}
        }

        side_effect = [None, mock_response]

        with mock.patch.object(self.service, '_make_api_call', side_effect=side_effect) as mocked_api:
            self.service.moex_base_urls = ['https://iss.moex.com', 'http://iss.moex.com']
            self.service.moex_url_templates = {'current': '/endpoint'}
            result = self.service.get_moex_price()

        self.assertEqual(result, 301.11)
        called_urls = [call.args[0] for call in mocked_api.call_args_list]
        self.assertEqual(called_urls, ['https://iss.moex.com/endpoint', 'http://iss.moex.com/endpoint'])


    def test_get_moex_price_respects_time_budget(self):
        with mock.patch.object(self.service, '_make_api_call', return_value=None) as mocked_api:
            self.service.moex_base_urls = ['https://iss.moex.com']
            self.service.moex_url_templates = {'current': '/a', 'prev': '/b'}
            self.service.moex_request_timeout = 1
            self.service.moex_retries = 1
            self.service.moex_max_total_seconds = 0

            result = self.service.get_moex_price()

        self.assertIsNone(result)
        self.assertEqual(mocked_api.call_count, 0)

    @mock.patch.object(SberPriceService, 'get_fair_price', return_value=None)
    @mock.patch.object(SberPriceService, 'get_moex_price', return_value=250.0)
    def test_get_current_data_handles_none_values(self, _mocked_moex, _mocked_fair):
        data = self.service.get_current_data()

        self.assertEqual(data['moex_price'], 250.0)
        self.assertIsNone(data['fair_price'])
        self.assertIsNone(data['fair_price_20_percent'])
        self.assertIsNone(data['pb_ratio'])
        self.assertEqual(data['price_score'], 'неизвестно')
