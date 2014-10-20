import unittest
from mock import patch, Mock, MagicMock, mock_open
from bs4 import BeautifulSoup
from StringIO import StringIO
from lib import to_unicode, to_str, get_counters, check_for_meta, fix_market_url, make_pycurl_request, get_url, \
    get_redirect_history, break_func_for_test, prepare_url


class InitTestCase(unittest.TestCase):
    pass

    def test_to_unicode1(self):
        res = to_unicode(u'unicode')
        self.assertTrue(isinstance(res, unicode))

    def test_to_unicode2(self):
        res = to_unicode('string')
        self.assertTrue(isinstance(res, unicode))

    def test_to_str1(self):
        val = u'unicode'
        errors='strict'
        res = to_str(val)
        self.assertEqual(res, val.encode('utf8', errors=errors) if isinstance(val, unicode) else val)

    def test_to_str2(self):
        val = 'string'
        errors='strict'
        res = to_str(val)
        self.assertEqual(res, val.encode('utf8', errors=errors) if isinstance(val, unicode) else val)

    def test_get_counters_matched(self):
        res = get_counters('somewords/counter.yadro.ru/hitsomewordsfdzhxfggoogle-analytics.com/ga.jssfsdgdgd')
        self.assertEqual(res, ['GOOGLE_ANALYTICS', 'LI_RU'])

    def test_get_counters_not_matched(self):
        res = get_counters('dfgsdhshstrhstrh')
        self.assertEqual(res, [])

    def test_check_for_meta(self):
        result = MagicMock(name="result")
        result.attrs = {
            "content": "somewords;url=url.ru/somepath",
            "http-equiv": 'refresh',
        }
        result.__getitem__ = Mock(return_value=result.attrs["content"])
        with patch.object(BeautifulSoup, "find", return_value=result):
            res = check_for_meta("content", "url")
        self.assertEqual(res, u'url.ru/somepath')

    def test_check_for_meta_no_result(self):
        result = MagicMock()
        result.attrs = {
            "http-equiv": 'refresh',
        }
        with patch.object(BeautifulSoup, "find", return_value=None):
            res = check_for_meta("content", "url")
        self.assertEqual(res, None)

    def test_check_for_meta_splitted_len_not_two(self):
        result = MagicMock()
        result.attrs = {
            "content": "somewords",
            "http-equiv": 'refresh',
        }
        result.__getitem__ = Mock(return_value=result.attrs["content"])
        with patch.object(BeautifulSoup, "find", return_value=result):
            res = check_for_meta("content", "url")
        self.assertEqual(res, None)

    def test_check_for_meta_not_m(self):
        result = MagicMock(name="result")
        result.attrs = {
            "content": "somewords;url=",
            "http-equiv": 'refresh',
        }
        result.__getitem__ = Mock(return_value=result.attrs["content"])
        with patch.object(BeautifulSoup, "find", return_value=result):
            res = check_for_meta("content", "url")
        self.assertEqual(res, None)

    def test_fix_market_url(self):
        res = fix_market_url("market://blablabla")
        self.assertEqual(res, 'http://play.google.com/store/apps/blablabla')

    def test_make_pycurl_request(self):
        curl = Mock()
        with patch('pycurl.Curl', Mock(curl)):
            with patch.object(StringIO, "getvalue", return_value='redirect_url'):
                content, redirect_url = make_pycurl_request('url', 5, 'useragent')
        self.assertTrue(content)
        self.assertTrue(redirect_url)

    def test_make_pycurl_request_no_useragent(self):
        curl = Mock()
        with patch('pycurl.Curl', Mock(curl)):
            with patch.object(StringIO, "getvalue", return_value='redirect_url'):
                content, redirect_url = make_pycurl_request('url', 5)
        self.assertTrue(content)
        self.assertTrue(redirect_url)

    def test_get_url(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', 'new_redirect_url'))):
            with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                prepare_url, redirect_type, content = get_url('url', 5, 'user_agent')
        self.assertEqual(prepare_url, 'prepare_url')
        self.assertEqual(redirect_type, 'http_status')
        self.assertEqual(content, 'content')

    def test_get_url_ok_redirect(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content',
                                                               'http://www.odnoklassniki.ru/sdfst.redirect'))):
            prepare_url, redirect_type, content = get_url('url', 5, 'user_agent')
        self.assertEqual(prepare_url, None)
        self.assertEqual(redirect_type, None)
        self.assertEqual(content, 'content')

    def test_get_url_not_ok_redirect(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', 'url'))):
            with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                prepare_url, redirect_type, content = get_url('url', 5, 'user_agent')
        self.assertEqual(prepare_url, 'prepare_url')
        self.assertEqual(redirect_type, 'http_status')
        self.assertEqual(content, 'content')

    def test_get_url_check_for_meta_ok(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', None))):
            with patch('lib.check_for_meta', Mock(return_value='new_redirect_url')):
                with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                    prepare_url, redirect_type, content = get_url('url', 5, 'user_agent')
        self.assertEqual(prepare_url, 'prepare_url')
        self.assertEqual(redirect_type, 'meta_tag')
        self.assertEqual(content, 'content')

    def test_get_url_check_for_meta_bad(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', None))):
            with patch('lib.check_for_meta', Mock(return_value=None)):
                with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                    prepare_url, redirect_type, content = get_url('url', 5, 'user_agent')
        self.assertEqual(prepare_url, 'prepare_url')
        self.assertEqual(redirect_type, None)
        self.assertEqual(content, 'content')

    def test_get_url_ok_urlsplit(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', 'market://url'))):
            with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                prepare_url, redirect_type, content = get_url('url', 5, 'user_agent')
        self.assertEqual(prepare_url, 'prepare_url')
        self.assertEqual(redirect_type, 'http_status')
        self.assertEqual(content, 'content')

    def test_get_url_exc(self):
        with patch('lib.make_pycurl_request', Mock(side_effect=ValueError('ValueError'))):
            self.assertRaises(Exception, get_url('url', 5, 'user_agent'))

    def test_get_redirect_history(self):
        with patch('lib.prepare_url', Mock(return_value='prepare_url')):
            with patch('lib.get_url', Mock(return_value=('redirect_url', 'redirect_type', 'content'))):
                with patch('lib.break_func_for_test', Mock(return_value=True)):
                    history_types, history_urls, counters = get_redirect_history('url', 5)
        self.assertEquals(history_types, ['redirect_type'])
        self.assertEquals(history_urls, ['prepare_url', 'redirect_url'])
        self.assertEquals(counters, [])

    def test_get_redirect_history_not_redirect_url(self):
        with patch('lib.prepare_url', Mock(return_value='prepare_url')):
            with patch('lib.get_url', Mock(return_value=(None, 'redirect_type', 'content'))):
                history_types, history_urls, counters = get_redirect_history('url', 5)
        self.assertEquals(history_types, [])
        self.assertEquals(history_urls, ['prepare_url'])
        self.assertEquals(counters, [])

    def test_get_redirect_history_redirect_type_error(self):
        with patch('lib.prepare_url', Mock(return_value='prepare_url')):
            with patch('lib.get_url', Mock(return_value=('redirect_url', 'ERROR', 'content'))):
                history_types, history_urls, counters = get_redirect_history('url', 5)
        self.assertEquals(history_types, ['ERROR'])
        self.assertEquals(history_urls, ['prepare_url', 'redirect_url'])
        self.assertEquals(counters, [])

    def test_get_redirect_history_matched(self):
        with patch('lib.prepare_url', Mock(return_value='http://www.odnoklassniki.ru/sdfst.redirect')):
            history_types, history_urls, counters = get_redirect_history('url', 5)
        self.assertEquals(history_types, [])
        self.assertEquals(history_urls, ['http://www.odnoklassniki.ru/sdfst.redirect'])
        self.assertEquals(counters, [])

    def test_prepare_url_url_is_none(self):
        res = prepare_url(None)
        self.assertEquals(res, None)

    def test_prepare_url(self):
        netlock = Mock()
        netlock.encode = Mock(side_effect=UnicodeError)
        with patch('lib.urlparse', Mock(return_value=('scheme', netlock, 'path', 'qs', 'anchor', 'fragments'))):
            with patch('lib.urlunparse', Mock()) as urlunparse:
                prepare_url('url')
        self.assertTrue(urlunparse.called)