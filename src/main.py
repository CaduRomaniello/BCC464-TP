import json
import os
from mip import *
from functions import solveCg, plotFacilities, readFile, solveCompact, write_cg_solutions, writeResults

def main():
    file_name = 'pmedcap1'

    file_dir = os.path.dirname(os.path.realpath('__file__'))

    instance = readFile(os.path.join(file_dir, f'./data/input/{file_name}.txt'))

    solutions_compact = []
    facilities_compact = []
    solutions_cg = []
    for i in range(len(instance["problems"])):
    # for i in range(1):
        print(f"> Problem number: {i + 1}")
        data_object, facilities_compact_object = solveCompact(instance["problems"][i], os.path.join(file_dir, f'./data/output/{file_name}/compact/data/'))

        cg_colution = solveCg(instance["problems"][i], os.path.join(file_dir, f'./data/output/{file_name}/cg/'), file_name)
        
        solutions_compact.append(data_object)
        facilities_compact.append(facilities_compact_object)
        solutions_cg.append(cg_colution)

    
    writeResults(os.path.join(file_dir, f'./data/output/{file_name}/compact/data/'), solutions_compact, facilities_compact)
    plotFacilities(facilities_compact, instance, file_name)
    write_cg_solutions(solutions_cg, os.path.join(file_dir, f'./data/output/{file_name}/cg/'))

if __name__ == '__main__':
    main()