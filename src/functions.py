from datetime import datetime
import json
import os
from matplotlib import pyplot as plt
from mip import *
import math

def readFile(FILE_NAME):
    instance = {
        "problems": []
    }
    
    file = open(FILE_NAME, "r")
    instance['num_problems'] = int(file.readline().rstrip().lstrip())

    for _ in range(instance['num_problems']):
        problem = {}

        line = file.readline().rstrip().lstrip()
        problem['problem_number'] = int(line.split(' ')[0])
        problem['best_solution'] = int(line.split(' ')[1])

        line = file.readline().rstrip().lstrip()
        problem['num_nodes'] = int(line.split(' ')[0])
        problem['num_medians'] = int(line.split(' ')[1])
        problem['median_capacity'] = int(line.split(' ')[2])

        problem['nodes'] = []
        for _ in range(problem['num_nodes']):
            line = file.readline().rstrip().lstrip()
            node = {
                'node_number': int(line.split(' ')[0]),
                'x': int(line.split(' ')[1]),
                'y': int(line.split(' ')[2]),
                'demand': int(line.split(' ')[3])
            }

            problem['nodes'].append(node)

        instance['problems'].append(problem)

    file.close()
    return instance

def generateDistanceMatrix(problem, matrix):
    N = problem['num_nodes']
    for i in range(N):
        for j in range(N):
            matrix[i][j] = math.floor((((problem['nodes'][i]['x'] - problem['nodes'][j]['x']) ** 2) + ((problem['nodes'][i]['y'] - problem['nodes'][j]['y']) ** 2)) ** 0.5)

def solveProblem(problem, path, file_name = "mip.lp"):
    N = problem['num_nodes']
    p = problem['num_medians']
    q = [problem['nodes'][i]['demand'] for i in range(N)]
    Q = problem['median_capacity']
    d = [[0 for _ in range(N)] for _ in range(N)]
    generateDistanceMatrix(problem, d)

    m = Model(sense=MINIMIZE, solver_name=CBC)
    m.verbose = 0

    x = [[m.add_var(var_type=BINARY, name=f"Node_{j}_satisfies_{i}") for i in range(N)] for j in range(N)] # x[i][j] = 1 if node j is attended by facility i
    y = [m.add_var(var_type=BINARY, name=f"Node_{j}_is_facility") for j in range(N)] # y[j] = 1 if node j is a facility

    m.objective = minimize(xsum(d[i][j] * x[i][j] for i in range(N) for j in range(N))) # minimize the sum of distances

    # all nodes should be attended by one and only one facility
    for i in range(N):
        m += xsum(x[i][j] for j in range(N)) == 1
    
    # the capacity of the facility should be greater or equal than the demand of its nodes
    for i in range(N):
        for j in range(N):
            m += q[i] * x[i][j] <= Q * y[j]

    # the number of facilities should be equal to p
    m += xsum(y[j] for j in range(N)) == p

    # optimize the model
    begin = datetime.now()
    status = m.optimize()
    end = datetime.now()

    exists = os.path.exists(path)
    if not exists:
        os.makedirs(path)

    m.write(f"{path}{problem['problem_number']}.lp")

    print(f"> Problem number: {problem['problem_number']}")
    print(f"  - Best solution  : {problem['best_solution']}")
    print(f"  - Objective value: {m.objective_value}")
    print(f"  - Gap            : {abs(((problem['best_solution'] - m.objective_value)) / problem['best_solution']) * 100:.2f}%")
    print(f"  - Execution time : {end - begin}\n")

    data_object = {
        "problem_number": problem['problem_number'],
        "best_solution": problem['best_solution'],
        "objective_value": m.objective_value,
        "gap": abs(((problem['best_solution'] - m.objective_value)) / problem['best_solution']) * 100,
        "execution_time": str(end - begin),
    }
    return data_object, createFacilitiesObject(m, x, y, problem)

def createFacilitiesObject(model, x, y, problem):
    returnObject = {
        "objective_value": model.objective_value,
        "facilities": []
    }

    for j in range(problem['num_nodes']):
        if y[j].x > 0.5:
            facility = {}
            facility['node_number'] = problem['nodes'][j]["node_number"]
            facility['attended_nodes'] = []
            for i in range(problem['num_nodes']):
                if x[i][j].x > 0.5:
                    facility['attended_nodes'].append(problem['nodes'][i]["node_number"])
            returnObject['facilities'].append(facility)
    
    return returnObject

def writeResults(path, solutions, facilities):
    for solution in solutions:
        file_dir = os.path.join(path, f'{solution["problem_number"]}_results.json')

        json_object = json.dumps(solution, indent = 4)

        with open(file_dir, "w") as outfile:
            outfile.write(json_object)

    for i in range(len(facilities)):
        file_dir = os.path.join(path, f'{i + 1}_facilities.json')

        json_object = json.dumps(facilities[i], indent = 4)

        with open(file_dir, "w") as outfile:
            outfile.write(json_object)

def plotFacilities(solutions, instance, file_name):
    # Plotando o resultado
    for i in range(len(solutions)):
        for j in range(len(solutions[i]['facilities'])):
            source_x = instance["problems"][i]["nodes"][solutions[i]['facilities'][j]['node_number'] - 1]['x']
            source_y = instance["problems"][i]["nodes"][solutions[i]['facilities'][j]['node_number'] - 1]['y']

            plt.plot(source_x, source_y, color="blue", zorder=0)

            for k in range(len(solutions[i]['facilities'][j]['attended_nodes'])):
                target_x = instance["problems"][i]["nodes"][solutions[i]['facilities'][j]['attended_nodes'][k] - 1]['x']
                target_y = instance["problems"][i]["nodes"][solutions[i]['facilities'][j]['attended_nodes'][k] - 1]['y']

                x_plot = [source_x, target_x]
                y_plot = [source_y, target_y]

                plt.plot(x_plot, y_plot, color="blue", zorder=0)
                plt.scatter(target_x, target_y, marker="o", color="green", s=15, zorder=5)

            plt.scatter(source_x, source_y, marker="o", color="red", s=15, zorder=5)
        
        # print(os.path.dirname(os.path.realpath('__file__')))
        plt.savefig(os.path.join(os.path.dirname(os.path.realpath('__file__')), f'./data/output/{file_name}/images/{instance["problems"][i]["problem_number"]}.png'))
        # plt.show()
        plt.close()
    
def solvePricing(problem, reduced_cost, tao, sub, dist):
    N = problem['num_nodes']

    pricing = Model("CPMP - CG - Pricing")
    pricing.verbose = False
    a = [pricing.add_var(f'loc{i + 1}_{sub}', var_type=BINARY) for i in range(N)]

    # print(f"  - Subproblem: {sub}")
    # print(f"  - len a: {len(a)}")
    # print(f"  - N: {N}")
    # print(f"  - len reduced_cost: {len(reduced_cost)}")
    # print(f"  - len matrix: {len(dist)} - {len(dist[0])}")
    pricing += xsum((dist[i][sub] - reduced_cost[i]) * a[i] for i in range(N)) - tao

    pricing += xsum(problem['nodes'][i]['demand'] * a[i] for i in range(N)) <= problem['median_capacity']
    pricing += a[sub] == 1

    pricing.optimize()
    return pricing

# solve the optimization problem of the p demias using pythom mip and column generation
def cg(problem, path, file_name = "mip.lp"):
    N = problem['num_nodes']
    p = problem['num_medians']
    q = [problem['nodes'][i]['demand'] for i in range(N)]
    Q = problem['median_capacity']
    d = [[0 for _ in range(N)] for _ in range(N)]
    generateDistanceMatrix(problem, d)
    EPS = 10e-4
    # print(EPS)

    lambdas = []
    constraints = []

    # model
    master = Model("CPMP - CG - Master", MINIMIZE, solver_name=CBC)
    master.verbose = False

    # artificial variables and restrictions
    y0 = master.add_var(obj=2000, name="artificial_var")
    for i in range(N):
        # lambdas.append(master.add_var(name=f'y{i}', obj=10000))
        constraints.append(master.add_constr(y0 == 1))

    r = master.add_constr(y0 * p == p)

    # objective function
    # master.optimize()
    # print(master.objective_value)
    # return {}, {}

    constraints.append(r)

    new_column = True

    count = 0
    while new_column:
        count += 1
        master.optimize()
        # print(f'iter - {count} ||| obj: {master.objective_value}')

        constraints_dual = []
        for i in constraints:
            constraints_dual.append(i.pi)
        tao = constraints_dual.pop()

        pricings = []
        for sub in range(N):
            pricings.append(solvePricing(problem, constraints_dual, tao, sub, d))
        
        new_column = False
        for j, pricing in enumerate(pricings):
            if pricing.objective_value < -EPS:
                # print(f'    -> pricing.objective_value: {pricing.objective_value} ||| EPS: {EPS} ||| isLess: {pricing.objective_value < -EPS}')
                vars = pricing.vars

                coeffs = []
                for i in vars:
                    coeffs.append(i.x)
                coeffs.append(1)

                column = Column(constraints, coeffs)
                obj = sum(d[i][j] for i in range(N) if vars[i].x > 0.5)
                lambdas.append(master.add_var(obj=obj, column=column, name=f'lambda_{len(lambdas)}'))
                new_column = True

    print(f"  - Objective value: {master.objective_value}")

    return {}, {}
