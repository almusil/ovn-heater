import ovn_stats
import time

active_context = None


ITERATION_STAT_NAME = 'Iteration Total'


class Context(object):
    def __init__(self, test_name, max_iterations=1, brief_report=False,
                 test=None):
        self.iteration = -1
        self.test_name = test_name
        self.max_iterations = max_iterations
        self.brief_report = brief_report
        self.iteration_start = None
        self.failed = False
        self.test = test

    def __enter__(self):
        global active_context
        print(f'***** Entering context {self.test_name} *****')
        ovn_stats.clear()
        active_context = self
        return self

    def __exit__(self, type, value, traceback):
        ovn_stats.report(self.test_name, brief=self.brief_report)
        print(f'***** Exiting context {self.test_name} *****')

    def __iter__(self):
        return self

    def __next__(self):
        now = time.perf_counter()
        if self.iteration_start:
            duration = now - self.iteration_start
            ovn_stats.add(ITERATION_STAT_NAME, duration, failed=self.failed)
            print(f'***** Context {self.test_name}, '
                  f'Iteration {self.iteration}, '
                  f'Result: {"FAILURE" if self.failed else "SUCCESS"} *****')
        self.failed = False
        if self.test:
            # exec external cmd
            self.test.exec_cmd(self.iteration, self.test_name)
        self.iteration_start = now
        if self.iteration < self.max_iterations - 1:
            self.iteration += 1
            print(f'***** Context {self.test_name}, '
                  f'Iteration {self.iteration} *****')
            return self.iteration
        raise StopIteration

    def fail(self):
        self.failed = True
