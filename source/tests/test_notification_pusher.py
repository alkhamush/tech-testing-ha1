import unittest
from mock import patch, Mock, MagicMock, mock_open
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
    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock_open()
        with patch('notification_pusher.open', m_open, create=True):
            with patch('os.getpid', Mock(return_value=pid)):
                with patch('notification_pusher.logger', Mock()):
                    notification_pusher.create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_wrong_config_filepath(self):
        with self.assertRaises(IOError): notification_pusher.load_config_from_pyfile('wrong/path')

    def test_parent_daemonize_first(self):
        with patch('os.fork', Mock(return_value=42)):
            with patch('os._exit', Mock()) as exit:
                with patch('notification_pusher.logger', Mock()):
                    notification_pusher.daemonize()
        self.assertTrue(exit.called)

    def test_parent_daemonize_second(self):
        with patch('os.fork', Mock(side_effect=OSError("OSError"))):
            with patch('notification_pusher.logger', Mock()):
                self.assertRaises(Exception, notification_pusher.daemonize)

    def test_daemonize_third(self):
        with patch('os.setsid', Mock()):
            with patch('os.fork', Mock(side_effect=[0, OSError("OSError")])):
                with patch('os._exit', Mock()):
                    with patch('notification_pusher.logger', Mock()):
                        self.assertRaises(Exception, notification_pusher.daemonize)

    def test_daemonize_fourth(self):
        with patch('os.setsid', Mock()) as setsid:
            with patch('os.fork', Mock(return_value=0)) as fork:
                with patch('os._exit', Mock()):
                    with patch('notification_pusher.logger', Mock()):
                        notification_pusher.daemonize()
        self.assertTrue(setsid.called)
        self.assertTrue(fork.called)

    def test_daemonize_fifth(self):
        with patch('os.setsid', Mock()) as setsid:
            with patch('os.fork', Mock(side_effect=[0, 1])) as fork:
                with patch('os._exit', Mock()):
                    with patch('notification_pusher.logger', Mock()):
                        notification_pusher.daemonize()
        self.assertTrue(setsid.called)
        self.assertTrue(fork.called)

    def test_parse_cmd_args_exist(self):
        parameters = ['--config', 'config']
        res = notification_pusher.parse_cmd_args(parameters)
        self.assertEquals(res.config, 'config')

    def test_my_execfile(self):
        with patch("__builtin__.execfile", Mock()):
            assert notification_pusher.my_execfile({}) == {}

    def test_load_configfile_successful(self):
        variables = {
            'PORT': '8080',
            'HOST': 'localhost'
        }
        with patch('notification_pusher.my_execfile', Mock(return_value=variables)):
            with patch('notification_pusher.logger', Mock()):
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
            with patch('notification_pusher.logger', Mock()):
                cfg = notification_pusher.load_config_from_pyfile("somepath")
        self.assertFalse(cfg == True)

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
            with patch('notification_pusher.logger', Mock()) as logger:
                notification_pusher.notification_worker(task,task_queue)
        self.assertTrue(logger.info.called)

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
            with patch('notification_pusher.logger', Mock()) as logger:
                notification_pusher.notification_worker(task, task_queue)
        self.assertTrue(logger.exception.called)

    def test_done_with_processed_tasks_success(self):
        task_queue = Mock()
        task_queue.qsize = Mock(return_value=10)
        task = Mock()
        task_queue.get_nowait = Mock(return_value=(task, 'action_name'))
        with patch('notification_pusher.logger', Mock()) as logger:
            notification_pusher.done_with_processed_tasks(task_queue)
        self.assertTrue(logger.debug.called)

    def test_done_with_processed_tasks_empty_except(self):
        task_queue = Mock()
        task_queue.qsize = Mock(return_value=10)
        task_queue.get_nowait = Mock(side_effect=gevent_queue.Empty())
        with patch('notification_pusher.logger', Mock()) as logger:
            notification_pusher.done_with_processed_tasks(task_queue)
        self.assertTrue(logger.debug.called)

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
                with patch('notification_pusher.break_func_for_test', Mock(return_value=True)):
                    with patch('notification_pusher.logger', Mock()) as logger:
                        notification_pusher.main_loop(config)
        self.assertTrue(logger.info.called)

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
                with patch('notification_pusher.sleep', Mock()):
                    with patch('notification_pusher.logger', Mock()) as logger:
                        notification_pusher.main_loop(config)
        self.assertTrue(logger.info.called)

    def test_install_signal_handlers(self):
        with patch('gevent.signal', Mock()):
            with patch('notification_pusher.logger', Mock()) as logger:
                notification_pusher.install_signal_handlers()
        self.assertTrue(logger.info.called)

    def test_main(self):
        with patch('source.notification_pusher.patch_all', Mock()):
            argv = ['1', '2', '3']
            args = Mock()
            args.daemon = True
            args.pidfile = "somepath"
            args.config = "somepath"
            with patch('notification_pusher.load_config_from_pyfile', Mock(return_value=self.get_config())):
                with patch('notification_pusher.parse_cmd_args', Mock(return_value=args)):
                    with patch('notification_pusher.patch_all', Mock()):
                        with patch('notification_pusher.dictConfig', Mock()):
                            with patch('notification_pusher.main_loop', Mock(side_effect=Exception)) as main_loop:
                                with patch('notification_pusher.sleep', Mock()):
                                    with patch('notification_pusher.logger', Mock()) as logger:
                                        with patch('notification_pusher.break_func_for_test', Mock(return_value=True)):
                                            notification_pusher.main(argv)
        self.assertTrue(logger.exception.called)
        self.assertTrue(main_loop.called)

    def test_main_no_while(self):
        with patch('source.notification_pusher.patch_all', Mock()):
            argv = ['1', '2', '3']
            args = Mock()
            args.daemon = False
            args.pidfile = None
            args.config = "somepath"
            with patch('notification_pusher.load_config_from_pyfile', Mock(return_value=self.get_config())):
                with patch('notification_pusher.parse_cmd_args', Mock(return_value=args)):
                    with patch('notification_pusher.patch_all', Mock()):
                        with patch('notification_pusher.dictConfig', Mock()):
                            with patch('notification_pusher.logger', Mock()) as logger:
                                with patch('notification_pusher.while_is_workig', Mock(return_value=False)):
                                        notification_pusher.main(argv)
        self.assertTrue(logger.info.called)

    def break_func_for_test(self):
        result = notification_pusher.break_func_for_test()
        self.assertFalse(result)




