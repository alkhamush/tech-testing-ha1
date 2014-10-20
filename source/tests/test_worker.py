__author__ = 'anis'

import unittest
from mock import patch, Mock, MagicMock
from tarantool.error import DatabaseError
from lib import worker


def get_confog():
    config = Mock()
    config.INPUT_QUEUE_HOST = "host1"
    config.INPUT_QUEUE_PORT = 80
    config.INPUT_QUEUE_SPACE = 42
    config.INPUT_QUEUE_TUBE = "name1"
    config.OUTPUT_QUEUE_HOST = "host2"
    config.OUTPUT_QUEUE_PORT = 8000
    config.OUTPUT_QUEUE_SPACE = 73
    config.OUTPUT_QUEUE_TUBE = "name2"
    config.QUEUE_TAKE_TIMEOUT = 5
    config.HTTP_TIMEOUT = 5
    config.MAX_REDIRECTS = 3
    config.USER_AGENT = "user_agent"
    return config


class WorkerTestCase(unittest.TestCase):
    def test_get_redirect_history_from_task_error_and_no_recheck1(self):
        task = Mock()
        task.data = dict(url='url', recheck=False, url_id='url_id', suspicious='suspicious')
        with patch('lib.worker.get_redirect_history', Mock(return_value=('ERROR', 'history_urls', 'counters'))):
            is_input, data = worker.get_redirect_history_from_task(task, 42)
            self.assertTrue(True, is_input)

    def test_get_redirect_history_from_task_error_and_no_recheck2(self):
        task = Mock()
        task.data = dict(url='url', recheck=True, url_id='url_id', suspicious='suspicious')
        with patch('lib.worker.get_redirect_history', Mock(return_value=('ERROR', 'history_urls', 'counters'))):
            is_input, data = worker.get_redirect_history_from_task(task, 42)
            self.assertFalse(is_input)

    def test_get_redirect_history_from_task_error_and_no_recheck3(self):
        task = Mock()
        task.data = dict(url='url', recheck=True, url_id='url_id')
        with patch('lib.worker.get_redirect_history', Mock(return_value=('ERROR', 'history_urls', 'counters'))):
            is_input, data = worker.get_redirect_history_from_task(task, 42)
            self.assertFalse(is_input)

    def test_worker_is_input_true(self):
        config = get_confog()
        with patch("os.path.exists", Mock(return_value=True)):
            with patch("lib.worker.break_func_for_test", Mock(return_value=True)):
                with patch("lib.worker.get_tube", Mock(return_value=MagicMock())):
                    data = dict(url='url', recheck=True, url_id='url_id', suspicious='suspicious')
                    with patch("lib.worker.get_redirect_history_from_task", Mock(return_value=(True, data))):
                        worker.worker(config, 42)

    def test_worker_is_input_false(self):
        config = get_confog()
        with patch("os.path.exists", Mock(return_value=True)):
            with patch("lib.worker.break_func_for_test", Mock(return_value=True)):
                with patch("lib.worker.get_tube", Mock(return_value=MagicMock())):
                    data = dict(url='url', recheck=True, url_id='url_id', suspicious='suspicious')
                    with patch("lib.worker.get_redirect_history_from_task", Mock(return_value=(False, data))):
                        worker.worker(config, 42)

    def test_worker_no_while(self):
        config = get_confog()
        with patch('lib.worker.logger', Mock()) as logger:
            with patch("os.path.exists", Mock(return_value=False)):
                worker.worker(config, 42)
        self.assertTrue(logger.info.called)

    def test_worker_ifresult_false(self):
        config = get_confog()
        with patch('lib.worker.logger', Mock()) as logger:
            with patch("os.path.exists", Mock(return_value=True)):
                with patch("lib.worker.break_func_for_test", Mock(return_value=True)):
                    with patch("lib.worker.get_tube", Mock(return_value=MagicMock())):
                        with patch("lib.worker.get_redirect_history_from_task", Mock(return_value=False)):
                            worker.worker(config, 42)
        self.assertTrue(logger.info.called)

    def test_worker_no_task(self):
        config = get_confog()
        input_tube = MagicMock()
        input_tube.take = Mock(return_value=False)
        with patch('lib.worker.logger', Mock()) as logger:
            with patch("os.path.exists", Mock(return_value=True)):
                with patch("lib.worker.break_func_for_test", Mock(return_value=True)):
                    with patch("lib.worker.get_tube", Mock(return_value=input_tube)):
                        worker.worker(config, 42)
        self.assertTrue(logger.info.called)

    def test_worker_exception(self):
        config = get_confog()
        task = MagicMock()
        task.ack = Mock(side_effect=DatabaseError)
        input_tube = MagicMock()
        input_tube.take = Mock(return_value=task)
        with patch('lib.worker.logger', Mock()) as logger:
            with patch("os.path.exists", Mock(return_value=True)):
                with patch("lib.worker.break_func_for_test", Mock(return_value=True)):
                    with patch("lib.worker.get_tube", Mock(return_value=input_tube)):
                        data = dict(url='url', recheck=True, url_id='url_id', suspicious='suspicious')
                        with patch("lib.worker.get_redirect_history_from_task", Mock(return_value=(True, data))):
                            worker.worker(config, 42)
        self.assertTrue(logger.info.called)

    def break_func_for_test(self):
        result = worker.break_func_for_test()
        self.assertFalse(result)