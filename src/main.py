import json
import os
from mip import *
from functions import plotFacilities, readFile, solveProblem, writeResults

def main():
    file_name = 'pmedcap1'

    file_dir = os.path.dirname(os.path.realpath('__file__'))

    instance = readFile(os.path.join(file_dir, f'./data/input/{file_name}.txt'))

    solutions = []
    facilities = []
    for i in range(len(instance["problems"])):
    # for i in range(1):
        data_object, facilities_object = solveProblem(instance["problems"][i], os.path.join(file_dir, f'./data/output/{file_name}/data/'), file_name)
        solutions.append(data_object)
        facilities.append(facilities_object)
    
    writeResults(os.path.join(file_dir, f'./data/output/{file_name}/data/'), solutions, facilities)
    plotFacilities(facilities, instance, file_name)

if __name__ == '__main__':
    main()