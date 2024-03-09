import logging


def configure_logging(verbose: int) -> None:
    if verbose == 0:
        fmt = "%(levelname)s: %(message)s"
        level = logging.WARNING
    elif verbose == 1:
        fmt = "%(levelname)s: %(message)s"
        level = logging.INFO
    else:
        fmt = "%(levelname)s: %(message)-50s (%(name)s#L%(lineno)d)"
        level = logging.DEBUG

    logging.basicConfig(format=fmt, level=level)
