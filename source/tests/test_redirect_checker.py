import unittest
from mock import patch, Mock
import redirect_checker


class RedirectCheckerTestCase(unittest.TestCase):
    pass
    def test_main_loop(self):
        test_config = Mock()
        test_config.WORKER_POOL_SIZE = 10
        test_config.SLEEP = 0.01
        test_config.CHECK_URL = 0.01
        test_pid = 42
        with patch('notification_pusher.logger', Mock()):
            with patch('os.getpid', Mock(return_value=test_pid)):
                with patch('redirect_checker.check_network_status', Mock(return_value=True)):
                    with patch('redirect_checker.active_children', Mock(return_value=list([1, 2, 3]))):
                        with patch('redirect_checker.spawn_workers', Mock()):
                            with patch('redirect_checker.sleep', Mock(side_effect=Exception())):
                                redirect_checker.main_loop(test_config)

    def test_main_loop_count_subzero(self):
        test_config = Mock()
        test_config.WORKER_POOL_SIZE = 2
        test_config.SLEEP = 0.01
        test_config.CHECK_URL = 0.01
        test_pid = 42
        with patch('notification_pusher.logger', Mock()):
            with patch('os.getpid', Mock(return_value=test_pid)):
                with patch('redirect_checker.check_network_status', Mock(return_value=True)):
                    with patch('redirect_checker.active_children', Mock(return_value=list([1, 2, 3]))):
                        with patch('redirect_checker.spawn_workers', Mock()):
                            with patch('redirect_checker.sleep', Mock(side_effect=Exception())):
                                redirect_checker.main_loop(test_config)


    def test_main_loop_check_network_status_false(self):
        test_config = Mock()
        test_config.WORKER_POOL_SIZE = 10
        test_config.SLEEP = 0.01
        test_config.CHECK_URL = 0.01
        test_pid = 42
        proc = Mock()
        proc.terminate = Mock()
        with patch('notification_pusher.logger', Mock()):
            with patch('os.getpid', Mock(return_value=test_pid)):
                with patch('redirect_checker.check_network_status', Mock(return_value=False)):
                    with patch('redirect_checker.active_children', Mock(return_value=list([proc, proc, proc]))):
                        with patch('redirect_checker.sleep', Mock(side_effect=Exception)):
                            redirect_checker.main_loop(test_config)

    def test_main_true(self):
        args = Mock()
        args.daemon = True
        args.pidfile = True
        config = Mock()
        config.LOGGING = Mock()
        config.EXIT_CODE = 0
        with patch('redirect_checker.parse_cmd_args', Mock(return_value=args)):
            with patch('redirect_checker.daemonize', Mock()) as daemonize:
                with patch('redirect_checker.create_pidfile', Mock()) as create_pidfile:
                    with patch('redirect_checker.dictConfig', Mock()) as dictConfig:
                        with patch('redirect_checker.main_loop', Mock()) as main_loop:
                            with patch('redirect_checker.load_config_from_pyfile', Mock(return_value=config)):
                                with patch('os.path.realpath', Mock()):
                                    with patch('os.path.expanduser', Mock()):
                                        res = redirect_checker.main('argv')
                                        self.assertTrue(daemonize.called)
                                        self.assertTrue(create_pidfile.called)
                                        self.assertTrue(dictConfig.called)
                                        self.assertTrue(main_loop.called)
                                        self.assertEqual(config.EXIT_CODE, res)

    def test_main_false(self):
        args = Mock()
        args.daemon = False
        args.pidfile = False
        config = Mock()
        config.LOGGING = Mock()
        config.EXIT_CODE = 0
        with patch('redirect_checker.parse_cmd_args', Mock(return_value=args)):
            with patch('redirect_checker.daemonize', Mock()) as daemonize:
                with patch('redirect_checker.create_pidfile', Mock()) as create_pidfile:
                    with patch('redirect_checker.dictConfig', Mock()) as dictConfig:
                        with patch('redirect_checker.main_loop', Mock()) as main_loop:
                            with patch('redirect_checker.load_config_from_pyfile', Mock(return_value=config)):
                                with patch('os.path.realpath', Mock()):
                                    with patch('os.path.expanduser', Mock()):
                                        res = redirect_checker.main('argv')
                                        self.assertFalse(daemonize.called)
                                        self.assertFalse(create_pidfile.called)
                                        self.assertTrue(dictConfig.called)
                                        self.assertTrue(main_loop.called)
                                        self.assertEqual(config.EXIT_CODE, res)

