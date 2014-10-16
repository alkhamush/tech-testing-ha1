import unittest
from mock import patch, Mock, MagicMock, mock_open
from bs4 import BeautifulSoup
from lib import to_unicode, to_str, get_counters, check_for_meta, fix_market_url, make_pycurl_request, get_url, \
    get_redirect_history, break_func_for_test, prepare_url


class InitTestCase(unittest.TestCase):

    def test_to_unicode1(self):
        to_unicode(u'unicode')

    def test_to_unicode1(self):
        to_unicode('string')

    def test_to_str1(self):
        to_str(u'unicode')

    def test_to_str2(self):
        to_str('string')

    def test_get_counters_matched(self):
        get_counters('somewords/counter.yadro.ru/hitsomewordsfdzhxfggoogle-analytics.com/ga.jssfsdgdgd')

    def test_get_counters_not_matched(self):
        get_counters('dfgsdhshstrhstrh')

    def test_check_for_meta(self):
        result = MagicMock(name="result")
        result.attrs = {
            "content": "somewords;url=url.ru/somepath",
            "http-equiv": 'refresh',
        }
        result.__getitem__ = Mock(return_value=result.attrs["content"])
        with patch.object(BeautifulSoup, "find", return_value=result):
            check_for_meta("content", "url")

    def test_check_for_meta_no_result(self):
        result = MagicMock()
        result.attrs = {
            "http-equiv": 'refresh',
        }
        result.__getitem__ = Mock(return_value=result.attrs["content"])
        with patch.object(BeautifulSoup, "find", return_value=result):
            check_for_meta("content", "url")

    def test_check_for_meta_splitted_len_not_two(self):
        result = MagicMock()
        result.attrs = {
            "content": "somewords",
            "http-equiv": 'refresh',
        }
        result.__getitem__ = Mock(return_value=result.attrs["content"])
        with patch.object(BeautifulSoup, "find", return_value=result):
            check_for_meta("content", "url")

    def test_check_for_meta_not_m(self):
        result = MagicMock(name="result")
        result.attrs = {
            "content": "somewords;url=",
            "http-equiv": 'refresh',
        }
        result.__getitem__ = Mock(return_value=result.attrs["content"])
        with patch.object(BeautifulSoup, "find", return_value=result):
            check_for_meta("content", "url")

    def test_fix_market_url(self):
        fix_market_url("market://blablabla")

    def test_make_pycurl_request(self):
        curl = Mock()
        curl.getinfo = Mock(return_value='redirect_url')
        with patch('pycurl.Curl', Mock(curl)):
            make_pycurl_request('url', 5, 'useragent')

    def test_make_pycurl_request_no_useragent(self):
        curl = Mock()
        curl.getinfo = Mock(return_value='redirect_url')
        with patch('pycurl.Curl', Mock(curl)):
            make_pycurl_request('url', 5)

    def test_get_url(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', 'new_redirect_url'))):
            with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                get_url('url', 5, 'user_agent')

    def test_get_url_ok_redirect(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content',
                                                                 'http://www.odnoklassniki.ru/sdfst.redirect'))):
            with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                get_url('url', 5, 'user_agent')

    def test_get_url_not_ok_redirect(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', 'url'))):
            with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                get_url('url', 5, 'user_agent')

    def test_get_url_check_for_meta_ok(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', None))):
            with patch('lib.check_for_meta', Mock(return_value='new_redirect_url')):
                with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                    get_url('url', 5, 'user_agent')

    def test_get_url_check_for_meta_bad(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', None))):
            with patch('lib.check_for_meta', Mock(return_value=None)):
                with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                    get_url('url', 5, 'user_agent')

    def test_get_url_ok_urlsplit(self):
        with patch('lib.make_pycurl_request', Mock(return_value=('content', 'market://url'))):
            with patch('lib.prepare_url', Mock(return_value='prepare_url')):
                get_url('url', 5, 'user_agent')

    def test_get_url_exc(self):
        with patch('lib.make_pycurl_request', Mock(side_effect=ValueError('ValueError'))):
            get_url('url', 5, 'user_agent')

    def test_get_redirect_history(self):
        with patch('lib.prepare_url', Mock(return_value='prepare_url')):
            with patch('lib.get_url', Mock(return_value=('redirect_url', 'redirect_type', 'content'))):
                with patch('lib.break_func_for_test', Mock(return_value=True)):
                    get_redirect_history('url', 5)

    def test_get_redirect_history_not_redirect_url(self):
        with patch('lib.prepare_url', Mock(return_value='prepare_url')):
            with patch('lib.get_url', Mock(return_value=(None, 'redirect_type', 'content'))):
                get_redirect_history('url', 5)

    def test_get_redirect_history_redirect_type_error(self):
        with patch('lib.prepare_url', Mock(return_value='prepare_url')):
            with patch('lib.get_url', Mock(return_value=('redirect_url', 'ERROR', 'content'))):
                get_redirect_history('url', 5)

    def test_get_redirect_history_matched(self):
        with patch('lib.prepare_url', Mock(return_value='http://www.odnoklassniki.ru/sdfst.redirect')):
            get_redirect_history('url', 5)

    def test_prepare_url_url_is_none(self):
        prepare_url(None)

    def test_prepare_url(self):
        netlock = Mock()
        netlock.encode = Mock(side_effect=UnicodeError)
        with patch('lib.urlparse', Mock(return_value=('scheme', netlock, 'path', 'qs', 'anchor', 'fragments'))):
            with patch('lib.urlunparse', Mock()):
                prepare_url('url')











