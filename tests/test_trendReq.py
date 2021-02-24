import json
from unittest.mock import Mock, patch

import pandas.api.types as ptypes
import proxy
from aiounittest import futurized, AsyncTestCase
from httpx import Response, Headers, ProxyError
from tenacity import RetryError

from pytrends_httpx.request import TrendReq

TIMEOUT = 30


class TestTrendReq(AsyncTestCase):

    async def test_get_data(self):
        """Should use same values as in the documentation"""
        pytrend = TrendReq()
        self.assertEqual(pytrend.hl, 'en-US')
        self.assertEqual(pytrend.tz, 360)
        self.assertEqual(pytrend.geo, '')

    async def test_get_cookies(self):
        """Should use same values as in the documentation"""
        pytrend = TrendReq()
        cookies = await pytrend.GetGoogleCookie()
        self.assertTrue(cookies['NID'])

    async def test_build_payload(self):
        """Should return the widgets to get data"""
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertIsNotNone(pytrend.token_payload)

    async def test__tokens(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertIsNotNone(pytrend.related_queries_widget_list)

    async def test_interest_over_time(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertIsNotNone(await pytrend.interest_over_time())

    async def test_interest_over_time_images(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'], gprop='images')
        self.assertIsNotNone(await pytrend.interest_over_time())

    async def test_interest_over_time_news(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'], gprop='news')
        self.assertIsNotNone(await pytrend.interest_over_time())

    async def test_interest_over_time_youtube(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'], gprop='youtube')
        self.assertIsNotNone(await pytrend.interest_over_time())

    async def test_interest_over_time_froogle(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'], gprop='froogle')
        self.assertIsNotNone(await pytrend.interest_over_time())

    async def test_interest_over_time_bad_gprop(self):
        pytrend = TrendReq()
        with self.assertRaises(ValueError):
            await pytrend.build_payload(kw_list=['pizza', 'bagel'], gprop=' ')

    async def test_interest_by_region(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertIsNotNone(await pytrend.interest_by_region())

    async def test_related_topics(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertIsNotNone(await pytrend.related_topics())

    async def test_related_queries(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertIsNotNone(await pytrend.related_queries())

    async def test_trending_searches(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertIsNotNone(await pytrend.trending_searches())

    async def test_top_charts(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertIsNotNone(await pytrend.top_charts(date=2019))

    async def test_suggestions(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertIsNotNone(await pytrend.suggestions(keyword='pizza'))

    async def test_ispartial_dtype(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        df = await pytrend.interest_over_time()
        assert ptypes.is_bool_dtype(df.isPartial)

    async def test_ispartial_dtype_timeframe_all(self):
        pytrend = TrendReq()
        await pytrend.build_payload(kw_list=['pizza', 'bagel'],
                                    timeframe='all')
        df = await pytrend.interest_over_time()
        assert ptypes.is_bool_dtype(df.isPartial)


class TestTrendReqRetries(AsyncTestCase):

    async def test_retries_5_times_with_no_success(self):
        mock_do_async_request = Mock(return_value=futurized(Exception('TestTrendReqRetries')))
        _do_async_request_patcher = patch('pytrends_httpx.request.TrendReq._do_async_request', mock_do_async_request)
        mocked_do_async_request = _do_async_request_patcher.start()
        pytrend = TrendReq(retries=5)
        with self.assertRaises(RetryError):
            await pytrend.build_payload(kw_list=['pizza', 'bagel'], timeframe='all')
        _do_async_request_patcher.stop()
        assert mocked_do_async_request.call_count == 5

    async def test_retries_5_times_with_4th_one_successful(self):
        _tokens_widgets_dict = {
            'widgets': []
        }
        _tokens_headers = Headers({'Content-Type': 'application/json'})
        _tokens_response = Response(status_code=200, headers=_tokens_headers, text='####{widgets_dict}'.format(widgets_dict=json.dumps(_tokens_widgets_dict)))
        mock_do_async_request = Mock()
        mock_do_async_request.side_effect = [futurized(Exception()), futurized(Exception()), futurized(Exception()), futurized(_tokens_response)]
        _do_async_request_patcher = patch('pytrends_httpx.request.TrendReq._do_async_request', mock_do_async_request)
        mocked_do_async_request = _do_async_request_patcher.start()
        pytrend = TrendReq(retries=5)
        self.assertIsNone(await pytrend.build_payload(kw_list=['pizza', 'bagel'], timeframe='all'))
        _do_async_request_patcher.stop()
        assert mocked_do_async_request.call_count == 4


class TestTrendReqWithProxies(AsyncTestCase):

    def run(self, result = None):
        with proxy.start(['--hostname', '127.0.0.1', '--port', '8899']):
            with proxy.start(['--hostname', '127.0.0.1', '--port', '8900']):
                with proxy.start(['--hostname', '127.0.0.1', '--port', '8901']):
                    super().run(result)

    async def test_send_req_through_proxy(self):
        pytrend = TrendReq(timeout=TIMEOUT, proxies=['http://127.0.0.1:8899'])
        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        resp = await pytrend.interest_over_time()
        self.assertIsNotNone(resp)

    async def test_proxy_cycling(self):
        proxies = ['http://127.0.0.1:8899', 'http://127.0.0.1:8900', 'http://127.0.0.1:8901']

        pytrend = TrendReq(timeout=TIMEOUT, proxies=proxies)
        last_proxy = pytrend._get_proxy()

        await pytrend.suggestions(keyword='pizza')
        curr_proxy = pytrend._get_proxy()
        self.assertNotEqual(curr_proxy, last_proxy)
        last_proxy = curr_proxy

        await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        await pytrend.interest_over_time()
        curr_proxy = pytrend._get_proxy()
        self.assertNotEqual(curr_proxy, last_proxy)

    async def test_raise_proxy_error_on_failure(self):
        proxies = ['http://127.0.0.1:2391']
        pytrend = TrendReq(timeout=TIMEOUT, proxies=proxies)
        with self.assertRaises(ProxyError):
            await pytrend.build_payload(kw_list=['pizza', 'bagel'])
        self.assertEqual(pytrend._get_proxy(), 'http://127.0.0.1:2391')
        self.assertEqual(len(pytrend.proxies), 1)

    async def test_leave_only_one_proxy_on_failure(self):
        proxies = ['http://127.0.0.1:2391', 'http://127.0.0.1:2390']
        pytrend = TrendReq(timeout=TIMEOUT, proxies=proxies)
        with self.assertRaises(ProxyError):
            await pytrend.build_payload(kw_list=['pizza', 'bagel'])
            await pytrend.interest_over_time()
        self.assertEqual(pytrend._get_proxy(), 'http://127.0.0.1:2390')
        self.assertEqual(len(pytrend.proxies), 1)
