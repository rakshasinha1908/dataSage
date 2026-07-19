class Operation:
    """
    Supported analytical operations.
    """

    # ----------------------------------------
    # Statistical Operations
    # ----------------------------------------

    MEAN = "mean"
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"

    # ----------------------------------------
    # Metadata Operations
    # ----------------------------------------

    DESCRIBE = "describe"
    COLUMNS = "columns"

    # ----------------------------------------
    # Dataset Operations
    # ----------------------------------------

    HEAD = "head"
    TAIL = "tail"
    SHOW_ROWS = "show_rows"

    ALL = {
        # Statistical
        MEAN,
        SUM,
        COUNT,
        MIN,
        MAX,

        # Metadata
        DESCRIBE,
        COLUMNS,

        # Dataset
        HEAD,
        TAIL,
        SHOW_ROWS,
    }