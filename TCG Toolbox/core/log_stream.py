import logging
import queue

LOG_QUEUE: queue.SimpleQueue[str] = queue.SimpleQueue()

class QueueLogHandler(logging.Handler):
    """A logging handler that pushes formatted log lines into a Python queue."""
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            LOG_QUEUE.put(msg)
        except Exception:
            pass
