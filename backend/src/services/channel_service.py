from ..models import Channel
from ..utils.serialize import record
def list_channels(db):return [record(c) for c in db.query(Channel).order_by(Channel.code)]
