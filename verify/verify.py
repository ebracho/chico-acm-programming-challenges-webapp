#!/usr/bin/env python3.5

import os, shutil, shlex, subprocess
from tempfile import TemporaryDirectory
import multiprocess as mp


supported_languages = ('c', 'c++', 'python', 'ruby', 'bash')
verify_dir = os.path.dirname(os.path.realpath(__file__))
run_script_path = os.path.join(verify_dir, 'run')


class UnsupportedLanguage(Exception):
    pass

class ProgramError(Exception):
    pass

class ProgramTimeout(Exception):
    pass


run_cmd = '{}/run {} {}'

def run_program(language, source, testinput, timeout=3):
    """Runs `source` with appropriate interpreter/compiler based on `langauge`
    in an nsjail. Passes `testinput` to program's. Raises `ProgramTimeout` if
    program executes for `timeout` seconds without terminating.
    """
    if language not in supported_languages:
        raise UnsupportedLanguage(language)

    with TemporaryDirectory() as program_dir:

        program_path = os.path.join(program_dir, 'program')
        testinput_path = os.path.join(program_dir, 'testinput')

        with open(program_path, 'w') as program_fd, open(testinput_path, 'w') as testinput_fd:
            program_fd.write(source)
            testinput_fd.write(testinput)

        args = shlex.split('{} {} {}'.format(run_script_path, language, program_dir))

        try:
            proc_obj = subprocess.run(
                args, timeout=timeout, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, universal_newlines=True)
        except subprocess.TimeoutExpired:
            raise ProgramTimeout()

    if proc_obj.returncode != 0:
        raise ProgramError(proc_obj.stderr)

    return proc_obj.stdout[:-1] # Remove trailing newline


def verify(language, source, testinput, testoutput, timeout=3):
    """Wrapper for `run_program` that compares program output with `testoutput`.
    Invokes `callback` with an appropriate status message after call to
    `run_program`."""
    try:
        output = run_program(language, source, testinput, timeout)
        status = 'PASS' if output == testoutput else 'FAIL'
    except UnsupportedLanguage as e:
        status = 'Unsupported language'
    except ProgramError as e:
        status = 'Program terminated due to error:\n {}'.format(str(e))
    except ProgramTimeout as e:
        status = 'Program timed out.'
    return status

