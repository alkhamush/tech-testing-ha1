import unittest
from mock import patch, Mock, MagicMock, mock_open
import socket
import urllib2
from lib import utils


class UtilsTestCase(unittest.TestCase):
    pass

    def test_daemonize_zero_pid1(self):
        with patch('os.fork', Mock(side_effect=[0, 1])):
            with patch('os.setsid', Mock()):
                with patch('os._exit', Mock()):
                    utils.daemonize()

    def test_daemonize_zero_pid2(self):
        with patch('os.fork', Mock(side_effect=[0, -1])):
            with patch('os.setsid', Mock()):
                with patch('os._exit', Mock()):
                    utils.daemonize()

    def test_daemonize_nonzero_pid(self):
        with patch('os.fork', Mock(return_value=10)):
            with patch('os._exit', Mock()):
                utils.daemonize()

    def test_daemonize_first_exc(self):
        exc = OSError("OSError")
        exc.errno = 1
        with patch('os.fork', Mock(side_effect=exc)):
            with patch('os._exit', Mock()):
                utils.daemonize()

    def test_daemonize_second_exc(self):
        exc = OSError("OSError")
        exc.errno = 1
        with patch('os.fork', Mock(side_effect=[0, exc])):
            with patch('os.setsid', Mock()):
                with patch('os._exit', Mock()):
                    utils.daemonize()

    def test_create_pidfile(self):
        m_open = mock_open()
        with patch('lib.utils.open', m_open, create=True):
            with patch('os.getpid', Mock(return_value=42)):
                utils.create_pidfile('/file/path')

    def test_my_execfile(self):
        with patch("__builtin__.execfile", Mock()):
            assert utils.my_execfile({}) == {}

    def test_load_configfile_successful(self):
        variables = {
            'PORT': '8080',
            'HOST': 'localhost'
        }
        with patch('lib.utils.my_execfile', Mock(return_value=variables)):
            utils.load_config_from_pyfile("somepath")

    def test_load_configfile_fail(self):
        variables = {
            'port': '8080',
            'host': 'localhost'
        }
        with patch('lib.utils.my_execfile', Mock(return_value=variables)):
            utils.load_config_from_pyfile("somepath")

    def test_parse_cmd_args_exist(self):
        parameters = ['--config', '--daemon', '--pid']
        parser = Mock()
        with patch('notification_pusher.argparse.ArgumentParser', Mock(return_value=parser)):
            utils.parse_cmd_args(parameters)

    def test_get_tube(self):
        utils.get_tube('host', 80, 5, 'name')

    def test_spawn_workers(self):
        with patch('lib.utils.Process', Mock(return_value=Mock())):
            utils.spawn_workers(10, 'target', 'args', 35)

    def test_check_network_status(self):
        with patch('lib.utils.urllib2.urlopen', Mock()):
            utils.check_network_status('url.com', 5)

    def test_check_network_status_exc(self):
        with patch('lib.utils.urllib2.urlopen', Mock(side_effect=(ValueError('value_error')))):
            utils.check_network_status('url.com', 5)



