import unittest
import time

from basin import Tasks

class TaskTestCase(unittest.TestCase):

    def test_create_task(self):
        tasks = Tasks()
        title = "My first task"
        tid = tasks.create(title=title)
        task = tasks.get_task(tid)
        self.assertEqual(task.title, title)

    def test_update_task(self):
        tasks = Tasks()
        misspelled_title = "My frist task"
        correct_title = "My first task"
        tid = tasks.create(title=misspelled_title)
        tasks.update(tid=tid, title=correct_title)
        task = tasks.get_task(tid)
        self.assertEqual(task.title, correct_title)

    def test_active(self):
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(tid in tasks.active_tids())
        tasks.complete(tid)
        self.assertTrue(tid not in tasks.active_tids())
        tasks.uncomplete(tid)
        self.assertTrue(tid in tasks.active_tids())
        tasks.trash(tid)
        self.assertTrue(tid not in tasks.active_tids())

    def test_complete(self):
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(tid not in tasks.completed_tids())
        tasks.complete(tid)
        self.assertTrue(tid in tasks.completed_tids())

    def test_trash(self):
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(tid not in tasks.trashed_tids())
        tasks.trash(tid)
        self.assertTrue(tid in tasks.trashed_tids())
        self.assertTrue(tid not in tasks.active_tids())
        tasks.sleep(tid)
        self.assertTrue(tid not in tasks.sleeping_tids())
        tasks.unsleep(tid)
        tasks.delegate(tid, "Bob")
        self.assertTrue(tid not in tasks.delegated_tids())
        tasks.undelegate(tid)
        tid2 = tasks.create()
        tasks.block(tid, tid2)
        self.assertTrue(tid not in tasks.blocked_tids())
        tasks.unblock(tid)
        tasks.complete(tid)
        self.assertTrue(tid not in tasks.completed_tids())

    def test_sleep(self):
        now = time.time()
        future = now + 1000000
        past = now - 1000000
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(tid not in tasks.sleeping_tids())
        tasks.sleep(tid, future)
        self.assertTrue(tid in tasks.sleeping_tids())
        tasks.unsleep(tid)
        self.assertTrue(tid not in tasks.sleeping_tids())
        tasks.sleep(tid)
        self.assertTrue(tid in tasks.sleeping_tids())
        tasks.unsleep(tid)
        self.assertTrue(tid not in tasks.sleeping_tids())
        tasks.sleep(tid, past)
        self.assertTrue(tid not in tasks.sleeping_tids())

    def test_block(self):
        tasks = Tasks()
        tid1 = tasks.create()
        tid2 = tasks.create()
        self.assertTrue(tid1 not in tasks.blocked_tids())
        self.assertTrue(tid2 not in tasks.blocked_tids())
        tasks.block(tid1, tid2)
        self.assertTrue(tid1 in tasks.blocked_tids())
        self.assertTrue(tid2 not in tasks.blocked_tids())
        tasks.unblock(tid1)
        self.assertTrue(tid1 not in tasks.blocked_tids())
        self.assertTrue(tid2 not in tasks.blocked_tids())
        tasks.block(tid1, tid2)
        tasks.unblock(tid1, tid2)
        self.assertTrue(tid1 not in tasks.blocked_tids())
        self.assertTrue(tid2 not in tasks.blocked_tids())

    def test_delegate(self):
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(tid not in tasks.delegated_tids())
        tasks.delegate(tid, 'Bob')
        self.assertTrue(tid in tasks.delegated_tids())
        tasks.undelegate(tid)
        self.assertTrue(tid not in tasks.delegated_tids())

    def test_infocus(self):
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(tid in tasks.infocus_tids())
        tasks.sleep(tid, time.time() + 1000000)
        self.assertTrue(tid not in tasks.infocus_tids())
        tasks.unsleep(tid)
        self.assertTrue(tid in tasks.infocus_tids())
        tid2 = tasks.create()
        tasks.block(tid, tid2)
        self.assertTrue(tid not in tasks.infocus_tids())
        tasks.unblock(tid)
        self.assertTrue(tid in tasks.infocus_tids())
        tasks.complete(tid)
        self.assertTrue(tid not in tasks.infocus_tids())
        tasks.uncomplete(tid)
        self.assertTrue(tid in tasks.infocus_tids())
        tasks.trash(tid)
        self.assertTrue(tid not in tasks.infocus_tids())
        tasks.untrash(tid)
        self.assertTrue(tid in tasks.infocus_tids())

if __name__ == '__main__':
    unittest.main()
