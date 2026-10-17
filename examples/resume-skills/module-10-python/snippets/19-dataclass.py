from dataclasses import dataclass, field, FrozenInstanceError
@dataclass(frozen=True)
class Request:
    tags: list[str] = field(default_factory=list)
a, b = Request(), Request()
a.tags.append('changed')
print(a.tags, b.tags)
try:
    a.tags = []
except FrozenInstanceError:
    print('rebinding rejected')
