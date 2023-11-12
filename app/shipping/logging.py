import logging


def add_logging_level(
    level_name: str, level: int, method_name: str, override: bool
) -> None:
    """Append logging module and logging class with missing attributes
    for specific logging level."""

    def instance_log(self, message, *args, **kwargs):
        if self.isEnabledFor(level):
            self._log(level, message, args, **kwargs)

    def module_log(message, *args, **kwargs):
        logging.log(level, message, *args, **kwargs)

    logging.addLevelName(level, level_name)

    if override or not hasattr(logging, level_name):
        setattr(logging, level_name, level)
    if override or not hasattr(logging.getLoggerClass(), method_name):
        setattr(logging.getLoggerClass(), method_name, instance_log)
    if override or not hasattr(logging, method_name):
        setattr(logging, method_name, module_log)


def add_trace_logging_level_if_not_exists(
    level_number: int = logging.DEBUG - 5,
):
    add_logging_level("TRACE", level_number, "trace", False)
