from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Dynamic:
    dynamic_id: str
    uid: str
    text: str
    publish_time: datetime
    url: str
    dynamic_type: str

    def to_dict(self) -> dict[str, str]:
        result = asdict(self)
        result["publish_time"] = self.publish_time.isoformat()
        return result
