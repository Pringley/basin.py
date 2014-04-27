import unittest
import time

from basin import Tasks

class TaskTestCase(unittest.TestCase):

    def test_create_task(self):
        tasks = Tasks()
        title = "My first task"
        tid = tasks.create(title)
        task = tasks.get(tid)
        self.assertEqual(task.title, title)

    def test_update_task(self):
        tasks = Tasks()
        misspelled_title = "My frist task"
        correct_title = "My first task"
        tid = tasks.create(title=misspelled_title)
        tasks.update(tid, title=correct_title)
        task = tasks.get(tid)
        self.assertEqual(task.title, correct_title)

    def test_complete(self):
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(not tasks.is_completed(tid))
        tasks.complete(tid)
        self.assertTrue(tasks.is_completed(tid))

    def test_trash(self):
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(not tasks.is_trashed(tid))
        tasks.trash(tid)
        self.assertTrue(tasks.is_trashed(tid))
        self.assertTrue(not tasks.is_active(tid))
        tasks.sleep(tid)
        self.assertTrue(tid not in tasks.filter(sleeping=True))
        tasks.unsleep(tid)
        tasks.delegate(tid, "Bob")
        self.assertTrue(tid not in tasks.filter(delegated=True))
        tasks.undelegate(tid)
        tid2 = tasks.create()
        tasks.block(tid, tid2)
        self.assertTrue(tid not in tasks.filter(blocked=True))
        tasks.unblock(tid)
        tasks.complete(tid)
        self.assertTrue(tid not in tasks.filter(completed=True))

    def test_sleep(self):
        now = time.time()
        future = now + 1000000
        past = now - 1000000
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(not tasks.is_sleeping(tid))
        tasks.sleep(tid, future)
        self.assertTrue(tasks.is_sleeping(tid))
        tasks.unsleep(tid)
        self.assertTrue(not tasks.is_sleeping(tid))
        tasks.sleep(tid)
        self.assertTrue(tasks.is_sleeping(tid))
        tasks.unsleep(tid)
        self.assertTrue(not tasks.is_sleeping(tid))
        tasks.sleep(tid, past)
        self.assertTrue(not tasks.is_sleeping(tid))

    def test_block(self):
        tasks = Tasks()
        tid1 = tasks.create()
        tid2 = tasks.create()
        self.assertTrue(not tasks.is_blocked(tid1))
        self.assertTrue(not tasks.is_blocked(tid2))
        tasks.block(tid1, tid2)
        self.assertTrue(tasks.is_blocked(tid1))
        self.assertTrue(not tasks.is_blocked(tid2))
        tasks.unblock(tid1)
        self.assertTrue(not tasks.is_blocked(tid1))
        self.assertTrue(not tasks.is_blocked(tid2))
        tasks.block(tid1, tid2)
        tasks.unblock(tid1, tid2)
        self.assertTrue(not tasks.is_blocked(tid1))
        self.assertTrue(not tasks.is_blocked(tid2))

    def test_delegate(self):
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(not tasks.is_delegated(tid))
        tasks.delegate(tid, 'Bob')
        self.assertTrue(tasks.is_delegated(tid))
        tasks.undelegate(tid)
        self.assertTrue(not tasks.is_delegated(tid))

    def test_active(self):
        tasks = Tasks()
        tid = tasks.create()
        self.assertTrue(tasks.is_active(tid))
        tasks.sleep(tid)
        self.assertTrue(not tasks.is_active(tid))
        tasks.unsleep(tid)
        self.assertTrue(tasks.is_active(tid))
        tid2 = tasks.create()
        tasks.block(tid, tid2)
        self.assertTrue(not tasks.is_active(tid))
        tasks.unblock(tid)
        self.assertTrue(tasks.is_active(tid))
        tasks.complete(tid)
        self.assertTrue(not tasks.is_active(tid))
        tasks.uncomplete(tid)
        self.assertTrue(tasks.is_active(tid))
        tasks.trash(tid)
        self.assertTrue(not tasks.is_active(tid))
        tasks.untrash(tid)
        self.assertTrue(tasks.is_active(tid))

    def test_history(self):
        tasks = Tasks()
        tid = tasks.create()
        title = "My first task"
        tasks.update(tid, title=title)
        tasks.sleep(tid)
        tasks.unsleep(tid)
        tasks.complete(tid)
        title2 = "My second task"
        tid2 = tasks.create(title=title2)
        history = tasks.dumps()
        tasks2 = Tasks.loads(history)
        self.assertTrue(tasks2.is_completed(tid))
        self.assertTrue(tasks2.is_active(tid2))
        self.assertEqual(title, tasks2.get(tid).title)
        self.assertEqual(title2, tasks2.get(tid2).title)

if __name__ == '__main__':
    unittest.main()
