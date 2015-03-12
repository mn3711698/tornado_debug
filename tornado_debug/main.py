# coding: utf8
import os
import sys


def run_program(args):

    if len(args) == 0:
        sys.exit(1)

    from tornado_debug import __file__ as root_directory

    root_directory = os.path.dirname(root_directory)
    boot_directory = os.path.join(root_directory, 'bootstrap')

    python_path = boot_directory

    if 'PYTHONPATH' in os.environ:
        path = os.environ['PYTHONPATH'].split(os.path.pathsep)
        if boot_directory not in path:
            python_path = "%s%s%s" % (boot_directory, os.path.pathsep,
                                      os.environ['PYTHONPATH'])

    os.environ['PYTHONPATH'] = python_path

    program_exe_path = args[0]

    if not os.path.dirname(program_exe_path):
        program_search_path = os.environ.get('PATH', '').split(os.path.pathsep)
        for path in program_search_path:
            path = os.path.join(path, program_exe_path)
            if os.path.exists(path) and os.access(path, os.X_OK):
                program_exe_path = path
                break

    os.execl(program_exe_path, *args)


def main():
    print "start tornado_debug"
    run_program(sys.argv[1:])
