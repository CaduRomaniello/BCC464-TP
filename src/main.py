import json
import os
from mip import *
from functions import readFile, solveProblem

def main():
    file_name = 'pmedcap1'

    file_dir = os.path.dirname(os.path.realpath('__file__'))

    instance = readFile(os.path.join(file_dir, f'./data/input/{file_name}.txt'))

    solveProblem(instance["problems"][0], os.path.join(file_dir, f'./data/output/{file_name}.lp'))

if __name__ == '__main__':
    main()