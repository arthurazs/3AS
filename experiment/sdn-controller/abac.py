import uuid
import vakt
from vakt.rules import Eq, Any, StartsWith, Not, Or

storage = vakt.MemoryStorage()

policy = vakt.Policy(
    str(uuid.uuid4()),
    subjects=[Eq('ied01')],
    actions=[{
        'type': Or(Eq('publish')),
        'dest': Eq('01:0c:cd:01:00:01')}],
    resources=[Eq('GOOSE')],
    effect=vakt.ALLOW_ACCESS,
)
storage.add(policy)

policy = vakt.Policy(
    str(uuid.uuid4()),
    subjects=[Eq('ied02')],
    actions=[{
        'type': Or(Eq('subscribe')),
        'dest': Eq('01:0c:cd:01:00:01')}],
    resources=[Eq('GOOSE')],
    effect=vakt.ALLOW_ACCESS,
)
storage.add(policy)

policy = vakt.Policy(
    str(uuid.uuid4()),
    subjects=[Any()],
    actions=[{'dest': Not(StartsWith('01:0c:cd:01'))}],
    resources=[Eq('GOOSE')],
    effect=vakt.DENY_ACCESS,
)
storage.add(policy)

guard = vakt.Guard(storage, vakt.RulesChecker())
