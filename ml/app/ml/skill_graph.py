def generate_skill_graph(skills):
    """
    Generates skill radar chart data
    """

    graph = {}

    for skill in skills:
        graph[skill] = 1

    return {
        "skill_graph": graph
    }