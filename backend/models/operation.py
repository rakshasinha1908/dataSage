class Operation:
    """
    Supported analytical operations.
    """

    # Statistical Operations
    MEAN = "mean"
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"

    # Dataset Operations
    HEAD = "head"
    TAIL = "tail"

    ALL = {
        MEAN,
        SUM,
        COUNT,
        MIN,
        MAX,
        HEAD,
        TAIL,
    }