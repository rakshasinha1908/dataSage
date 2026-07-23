from models.operation import Operation


EXPLAINABLE_OPERATIONS = {
    Operation.SUM,
    Operation.MEAN,
    Operation.COUNT,
    Operation.MIN,
    Operation.MAX,
}


def is_explainable(query_context):

    if query_context is None:
        return False

    return query_context.query_plan.operation in EXPLAINABLE_OPERATIONS