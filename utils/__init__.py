import random
import json
import os
from threading import Timer, Event, Thread

class PersistedDict(dict):
    def __init__(self, file_path, overwrite=False):
        super(PersistedDict, self).__init__()
        self.file_path = os.path.abspath(os.path.expanduser(file_path))
        self.read_from_file(overwrite=overwrite)

    def read_from_file(self, overwrite):
        if os.path.exists(self.file_path):
            if not overwrite:
                with open(self.file_path, 'r') as f:
                    data = f.read()
                    if data:
                        self.update(json.loads(data))

            # Write a backup file in case something goes wrong
            with open(self.file_path + '~', 'w+') as f:
                f.write(json.dumps(self))

    def save(self):
        with open(self.file_path, 'w+') as f:
            f.write(json.dumps(self))

class MultiThreadObject(object):
    '''
    On start() this object shoots off two threads. One that prompts the user for input, and
    another that continually calls the object's tick() method. Both the tick method and
    commands invoked by the user are executed on the thread that originally invoked start
    on the object which blocks until it has something to do.

    NOTE: This is needed to deal with some bugginess I found with the win32com interface
    used for accessing iTunes. It seems to break whenever you try and access the
    interface on a thread other than the one that created it. Ideally I would put the
    workaround in the ItunesWrapper, unfortunately trying to instantiate the COM
    object on anything OTHER than the main thread causes it to fail as well. So for the
    time being I'm forced to put the workaround here, which really shouldn't care about
    problems in the wrapper.
    '''

    TICK_INTERVAL = 1.0
    PROMPT = ""
    COMMANDS = {}
    STOP_COMMAND = 'q'

    def __init__(self):
        self.main_thread_event = Event()
        self.main_thread_command = None
        self.main_thread_args = []
        self.stopped = False

    def start(self):
        def wrapper():
            self.__tick__()
            self.tick_timer = Timer(self.TICK_INTERVAL, wrapper)
            self.tick_timer.start()

        self.tick_timer = Timer(self.TICK_INTERVAL, wrapper)
        self.tick_timer.start()

        self.input_thread = Thread(target=self.check_for_input)
        self.input_thread.start()

        while True:
            self.main_thread_event.wait()
            self.main_thread_command(*self.main_thread_args)
            self.main_thread_event.clear()

            if self.stopped:
                break

    def __stop__(self):
        self.stopped = True
        self.input_thread.join()
        self.tick_timer.cancel()

        self.stop()

    def check_for_input(self):
        while True:
            user_input = raw_input(self.PROMPT)

            try:
                args = [int(user_input)]
                fn = getattr(self, self.DIGIT_COMMAND)
            except ValueError:
                if ' ' in user_input:
                    command = user_input[:user_input.index(' ')]
                    # Just take everything passed the first space as a single arg
                    # should add better parsing for multiple args
                    args = [user_input[user_input.index(' ') + 1:]]
                else:
                    command = user_input
                    args = None

                if command == self.STOP_COMMAND:
                    self.execute_on_main_thread(self.__stop__)
                    break
                elif command in self.COMMANDS:
                    fn = getattr(self, self.COMMANDS[command])

            self.execute_on_main_thread(fn, args)

    def execute_on_main_thread(self, call, args=None):
        self.main_thread_command = call
        self.main_thread_args = args or []
        self.main_thread_event.set()

    def __tick__(self):
        self.execute_on_main_thread(self.tick)

    def tick(self):
        raise NotImplemented()
