class Operation:
    """
    Supported analytical operations.
    """

    MEAN = "mean"
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"

    ALL = {
        MEAN,
        SUM,
        COUNT,
        MIN,
        MAX,
    }