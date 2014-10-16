import unittest
import mock
from mock import patch, Mock, MagicMock
import notification_pusher
from lib.utils import Config
from requests import RequestException
from gevent import queue as gevent_queue
from threading import current_thread
import os
from gevent import sleep
import tarantool
import tarantool_queue


def start_app():
    notification_pusher.run_application = True


def stop_app():
    notification_pusher.run_application = False


class NotificationPusherTestCase(unittest.TestCase):
    pass
    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with patch('notification_pusher.open', m_open, create=True):
            with patch('os.getpid', Mock(return_value=pid)):
                notification_pusher.create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_wrong_config_filepath(self):
        with self.assertRaises(IOError): notification_pusher.load_config_from_pyfile('wrong/path')

    def test_parent_daemonize_first(self):
        with patch('os.fork', Mock(return_value=42)):
            with patch('os._exit', Mock()):
                notification_pusher.daemonize()

    def test_parent_daemonize_second(self):
        with patch('os.fork', Mock(side_effect=OSError("OSError"))):
            self.assertRaises(Exception, notification_pusher.daemonize)

    def test_daemonize_third(self):
        with patch('os.setsid', mock.Mock()):
            with patch('os.fork', Mock(side_effect=[0, OSError("OSError")])):
                with patch('os._exit', Mock()):
                    self.assertRaises(Exception, notification_pusher.daemonize)

    def test_daemonize_fourth(self):
        with patch('os.setsid', Mock()):
            with patch('os.fork', Mock(return_value=0)):
                with patch('os._exit', Mock()):
                    notification_pusher.daemonize()

    def test_daemonize_fifth(self):
        with patch('os.setsid', mock.Mock()):
            with patch('os.fork', Mock(side_effect=[0, 1])):
                with patch('os._exit', Mock()):
                    notification_pusher.daemonize()

    def test_parse_cmd_args_exist(self):
        parameters = ['--config', '--daemon', '--pid']
        parser = Mock()
        with patch('notification_pusher.argparse.ArgumentParser', Mock(return_value=parser)):
            notification_pusher.parse_cmd_args(parameters)

    def test_my_execfile(self):
        with mock.patch("__builtin__.execfile", mock.Mock()):
            assert notification_pusher.my_execfile({}) == {}

    def test_load_configfile_successful(self):
        variables = {
            'PORT': '8080',
            'HOST': 'localhost'
        }
        with patch('notification_pusher.my_execfile', Mock(return_value=variables)):
            cfg = notification_pusher.load_config_from_pyfile("somepath")
        real_config = notification_pusher.Config()
        real_config.PORT = variables['PORT']
        real_config.HOST = variables['HOST']
        self.assertEqual(cfg.PORT, real_config.PORT)
        self.assertEqual(cfg.HOST, real_config.HOST)

    def test_load_configfile_fail(self):
        variables = {
            'port': '8080',
            'host': 'localhost'
        }
        with patch('notification_pusher.my_execfile', Mock(return_value=variables)):
            cfg = notification_pusher.load_config_from_pyfile("somepath")
        real_config = notification_pusher.Config()
        real_config.port = variables['port']
        real_config.host = variables['host']
        self.assertEqual(cfg.port, real_config.port)
        self.assertEqual(cfg.host, real_config.host)

    def test_notification_worker_success(self):
        task = Mock()
        task_queue = Mock()
        data = {
            "callback_url": "www.url.ru",
            "id": 42
        }
        task.data = data
        task.task_id = 42
        with patch('requests.post', Mock(return_value=Mock(name = "response"))):
            notification_pusher.notification_worker(task,task_queue)

    def test_notification_worker_unsuccess(self):
        task = Mock()
        task_queue = Mock()
        data = {
            "callback_url": "www.url.ru",
            "id": 42
        }
        task.data = data
        task.task_id = 42
        with patch('requests.post', Mock(side_effect=RequestException("RequestException"))):
             notification_pusher.notification_worker(task, task_queue)

    def test_done_with_processed_tasks_success(self):
        task_queue = Mock()
        task_queue.qsize = Mock(return_value=10)
        task = Mock()
        task_queue.get_nowait = Mock(return_value=(task, 'action_name'))
        notification_pusher.done_with_processed_tasks(task_queue)

    def test_done_with_processed_tasks_empty_except(self):
        task_queue = Mock()
        task_queue.qsize = Mock(return_value=10)
        task_queue.get_nowait = Mock(side_effect=gevent_queue.Empty())
        notification_pusher.done_with_processed_tasks(task_queue)

    def test_stop_handler_exit_code(self):
        signum = 42
        exit_code = notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum
        notification_pusher.stop_handler(signum)
        self.assertEqual(exit_code, notification_pusher.exit_code)

    def get_config(self):
        config = Config()
        config.QUEUE_HOST = 'localhost'
        config.QUEUE_PORT = 8080
        config.QUEUE_SPACE = 5
        config.QUEUE_TAKE_TIMEOUT = 0.07
        config.QUEUE_TUBE = 'some_tube'
        config.HTTP_CONNECTION_TIMEOUT = 10
        config.SLEEP = 0.01
        config.SLEEP_ON_FAIL = 5
        config.WORKER_POOL_SIZE = 15
        config.LOGGING = 5
        return config

    def test_main_loop_successful_while(self):
        config = self.get_config()
        worker = Mock()
        worker.start = Mock(return_value=1)
        task = Mock()
        task.task_id = Mock(return_value=1)
        tube = Mock()
        tube.take = Mock(return_value=task)
        queue = Mock()
        queue.tube = Mock(return_value=tube)
        with patch('notification_pusher.tarantool_queue.Queue', Mock(return_value=queue)):
            with patch('notification_pusher.Greenlet', Mock(return_value=worker)):
                with patch('notification_pusher.sleep', Mock(side_effect=Exception)):
                    notification_pusher.main_loop(config)

    def test_main_loop_unsuccessful_while(self):
        config = self.get_config()
        worker = Mock()
        worker.start = Mock(return_value=1)
        task = Mock()
        task.task_id = Mock(return_value=1)
        tube = Mock()
        tube.take = Mock(return_value=task)
        queue = Mock()
        queue.tube = Mock(return_value=tube)
        Mock(stop_app())
        with patch('notification_pusher.tarantool_queue.Queue', Mock(return_value=queue)):
            with patch('notification_pusher.Greenlet', Mock(return_value=worker)):
                with patch('gevent.sleep', Mock()):
                    notification_pusher.main_loop(config)

    def test_install_signal_handlers(self):
        with patch('gevent.signal', Mock()):
            notification_pusher.install_signal_handlers()

    def test_main_without_args(self):
        with patch('source.notification_pusher.patch_all', Mock()):
            argv = ['1', '2', '3']
            args = Mock()
            args.daemon = True
            args.pidfile = "somepath"
            args.config = "somepath"
            with patch('notification_pusher.parse_cmd_args', Mock(return_value=args)):
                with patch('notification_pusher.load_config_from_pyfile',
                           Mock(return_value=self.get_config())):
                    with patch('notification_pusher.dictConfig', Mock()):
                        with patch('notification_pusher.main_loop', Mock(side_effect=Exception)):
                            with patch('notification_pusher.logger', Mock()):
                                with patch('gevent.sleep', Mock()):
                                    notification_pusher.main(argv)




