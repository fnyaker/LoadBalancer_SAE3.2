# -*- coding: utf-8 -*-
"""
A convenience module for shelling out with realtime output
includes:
- subprocess - Works with additional processes.
- shlex - Lexical analysis of shell-style syntaxes.
"""

from subprocess import Popen, PIPE
import shlex
import fcntl
import os


def run(command):
    process = Popen(command, stdout=PIPE, shell=True)
    while True:
        line = process.stdout.readline().rstrip()
        if not line:
            break
        yield line.decode('utf-8')

def run_command(command):
    process = Popen(shlex.split(command), stdout=PIPE)
    while True:
        output = process.stdout.readline().rstrip().decode('utf-8')
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc



if __name__ == "__main__":
    for path in run("python -u temp_code_a2d4561b40204533a6b9c17839205724.py"):
        print("Output : ",path)
    #run("python temp_code_a2d4561b40204533a6b9c17839205724.py")