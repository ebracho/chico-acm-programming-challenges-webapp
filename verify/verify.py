#!/usr/bin/env python3.5

import os, shutil, shlex, subprocess
from tempfile import TemporaryDirectory
import multiprocessing as mp


supported_languages = ('c', 'c++', 'python', 'ruby', 'bash')
verify_dir = os.path.dirname(os.path.realpath(__file__))
entry_script_path = os.path.join(verify_dir, 'entry')


class UnsupportedLanguage(Exception):
    pass

class ProgramError(Exception):
    pass

class ProgramTimeout(Exception):
    pass


docker_run_cmd = 'docker run --net=none -m 500m --ulimit nproc=30 \
    -v {0}:/home/unprivileged -w /home/unprivileged -e LANGUAGE={1} \
    verify /bin/bash entry'

def run_program(language, source, testinput, timeout=3):
    """
    Launches docker container to run `source` with given `language` and 
    `testinput`. Returns stdout of program.
    """
    if language not in supported_languages:
        raise UnsupportedLanguage(language)

    # Create program directory to be copied to docker container
    with TemporaryDirectory() as program_dir:

        program_path = os.path.join(program_dir, 'program')
        testinput_path = os.path.join(program_dir, 'testinput')

        with open(program_path, 'w') as program_fd, open(testinput_path, 'w') as testinput_fd:
            program_fd.write(source)
            testinput_fd.write(testinput)

        # Copy entry script
        shutil.copyfile(entry_script_path, os.path.join(program_dir, 'entry'))

        # Build docker-run command
        args = shlex.split(docker_run_cmd.format(program_dir, language))

        try:
            proc_obj = subprocess.run(
                args, timeout=timeout, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, universal_newlines=True)
        except subprocess.TimeoutExpired:
            raise ProgramTimeout()

    if proc_obj.returncode != 0:
        raise ProgramError(proc_obj.stderr)

    return proc_obj.stdout[:-1] # Remove trailing newline


def verify(language, source, testinput, testoutput, callback, timeout=3):
    """
    Wrapper for `run_program` that compares program output with `testoutput`.
    Invokes `callback` with an appropriate status message after call to
    `run_program`.
    """
    try:
        output = run_program(language, source, testinput, timeout)
        status = 'PASS' if output == testoutput else 'FAIL'
    except UnsupportedLanguage as e:
        status = 'Unsupported language'
    except ProgramError as e:
        status = 'Program terminated due to error.'
    except ProgramTimeout as e:
        status = 'Program timed out.'
    callback(status=status)


"""
Concurrent task queue for `verify`. 
"""
class VerifyQueue:
    queue = mp.JoinableQueue()

    def __init__(self, processes=None):
        """
        Specify the number of worker processes to pull from the task queue.
        Defaults to os.cpu_count()
        """
        self.pool = mp.Pool(processes, VerifyQueue._worker_hook, (self.queue,))

    def put(self, language, source, testinput, testoutput, callback, timeout=3):
        """
        Put a verify task at the end of the task queue.
        """
        self.queue.put((language, source, testinput, testoutput, callback, timeout))

    def join(self):
        """
        Block until all tasks on the queue have completed.
        """
        self.queue.join()

    @staticmethod
    def _worker_hook(task_queue):
        while True:
            args = task_queue.get(block=True)
            verify(*args)
            task_queue.task_done()
        
    def __del__(self):
        self.join()
        self.pool.close()
