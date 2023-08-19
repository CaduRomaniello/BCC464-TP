from mip import *

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
            matrix[i][j] = ((problem['nodes'][i]['x'] - problem['nodes'][j]['x']) ** 2 + (problem['nodes'][i]['y'] - problem['nodes'][j]['y']) ** 2) ** 0.5

def solveProblem(problem, FILE_NAME = "mip.lp"):
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
    status = m.optimize()
    m.write(f"{FILE_NAME}.lp")

    print(f"Objective value: {m.objective_value}")
    return createReturnObject(m, x, y, problem)

def createReturnObject(model, x, y, problem):
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
    