import json
import logging
from datetime import UTC, datetime

from apps.core.middleware import current_request_id

# What every LogRecord has; anything else on a record came from `extra`.
STANDARD_ATTRIBUTES = frozenset(
    vars(logging.LogRecord('', 0, '', 0, '', None, None))
) | {'message', 'asctime'}


class RequestIdFilter(logging.Filter):
    """Puts the request's id on every line logged while it runs."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id.get()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON line per event, its traceback inside (stage logs, CloudWatch)."""

    def format(self, record: logging.LogRecord) -> str:
        moment = datetime.fromtimestamp(record.created, UTC)
        event = {
            'time': moment.isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        event |= {
            key: value
            for key, value in vars(record).items()
            if key not in STANDARD_ATTRIBUTES
        }
        if record.exc_info:
            event['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(event, ensure_ascii=False, default=str)
