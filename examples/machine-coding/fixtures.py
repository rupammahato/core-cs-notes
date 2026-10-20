"""Authored contracts and expected outcomes, independent of the compiled runner."""
from pathlib import Path

BASE = Path(__file__).resolve().parent
MODES = ['kv', 'limiter', 'bus', 'scheduler', 'vending', 'booking', 'search', 'flags']


def error(message):
    return {'__error': message}


def case(mode, title, reasoning, trap, follow_up, steps):
    return dict(mode=mode, title=title, reasoning=reasoning, trap=trap, follow_up=follow_up,
                commands=[command for command, _ in steps],
                expected=[{'ok': False, 'error': value['__error']} if isinstance(value, dict) and '__error' in value
                          else {'ok': True, 'result': value} for _, value in steps])


CASES = [
    case('kv', 'A nested commit is still inside its parent',
         'BEGIN saves the current map. Committing the inner frame discards only its snapshot; the outer snapshot still contains the original value.',
         'Discarding every snapshot on inner COMMIT silently changes the contract.',
         'How would an undo log reduce the cost of BEGIN?', [
             ('SET name original', None), ('BEGIN', None), ('SET name outer', None), ('BEGIN', None),
             ('SET name inner', None), ('COMMIT', None), ('GET name', 'inner'), ('ROLLBACK', None),
             ('STATE', {'data': {'name': 'original'}, 'depth': 0})]),
    case('kv', 'Empty value and missing key differ',
         'An optional value distinguishes a present empty string from no mapping. Erasing a missing key is a successful no-op returning false.',
         'Using an empty string as the missing-value sentinel loses information.',
         'What should a DELETE API return for an absent key?', [
             ('SET k ""', None), ('GET k', ''), ('GET absent', None), ('ERASE k', True), ('ERASE k', False)]),
    case('kv', 'Rollback restores deletion and insertion',
         'The snapshot restores the complete key set, so an erased old key returns and a newly inserted key disappears.',
         'Restoring updated values alone misses inserted and deleted keys.',
         'How do tombstones help an undo-log implementation?', [
             ('SET a one', None), ('BEGIN', None), ('ERASE a', True), ('SET b two', None),
             ('ROLLBACK', None), ('STATE', {'data': {'a': 'one'}, 'depth': 0})]),
    case('kv', 'Invalid commands preserve the map',
         'Both transaction preconditions and the full command arity are checked before mutation.',
         'Ignoring trailing arguments can accept a malformed write.',
         'What is the difference between domain rejection and allocation failure?', [
             ('SET a safe', None), ('COMMIT', error('no transaction')), ('ROLLBACK', error('no transaction')),
             ('SET a bad extra', error('wrong arity')), ('STATE', {'data': {'a': 'safe'}, 'depth': 0})]),
    case('limiter', 'The oldest accepted request expires exactly at the boundary',
         'The active interval is (now-window, now]. At time 10 the request at 0 is outside a width-10 window, while the request at 9 remains.',
         'Using < instead of <= when pruning counts an expired request.',
         'Would a closed interval change your test expectation?', [
             ('INIT 2 10', None), ('ALLOW user 0', True), ('ALLOW user 9', True),
             ('ALLOW user 9', False), ('ALLOW user 10', True), ('ALLOW user 10', False)]),
    case('limiter', 'Users have separate quotas',
         'The accepted histories are keyed by user. A denied attempt does not add another timestamp.',
         'A single global deque accidentally makes unrelated users share a quota.',
         'How would you add a second global quota without partial consumption?', [
             ('INIT 1 5', None), ('ALLOW a 0', True), ('ALLOW a 1', False),
             ('ALLOW b 1', True), ('ALLOW a 5', True)]),
    case('limiter', 'A regressing clock is rejected',
         'Time is globally nondecreasing for this limiter instance. An invalid timestamp is rejected before pruning or inserting.',
         'Sorting timestamps after accepting them hides a broken clock contract.',
         'Which clock would you inject in a real single-process service?', [
             ('INIT 1 10', None), ('ALLOW a 10', True), ('ALLOW b 9', error('time regressed')),
             ('ALLOW b 10', True), ('ALLOW a 19', False), ('ALLOW a 20', True)]),
    case('limiter', 'Failed initialization can be retried',
         'The optional service becomes engaged only after a valid constructor completes. Initialization is then immutable.',
         'Setting an initialized flag before validation can brick the service.',
         'How would you safely change a running limiter policy?', [
             ('ALLOW a 0', error('initialize first')), ('INIT 0 10', error('invalid limit')),
             ('INIT 1 10', None), ('INIT 2 10', error('already initialized')), ('ALLOW a 0', True)]),
    case('bus', 'One callback failure does not stop delivery',
         'Each matching callback runs in subscription order and is isolated by its own exception handler. Other topics are ignored.',
         'A catch around the entire loop skips later callbacks after the first throw.',
         'Should a caller receive aggregate failures, or should they go to telemetry?', [
             ('SUB a orders record x', None), ('SUB b orders throw x', None), ('SUB c other record x', None),
             ('SUB d orders record x', None), ('PUB orders paid',
              {'callbacks': ['a:ok', 'b:error', 'd:ok'], 'events': ['a:paid', 'b:paid', 'd:paid']})]),
    case('bus', 'Unsubscribe changes the next dispatch',
         'The copied callback list owns this dispatch. Removing b while a runs does not remove b from the current snapshot.',
         'Iterating the live vector while erasing subscriptions can invalidate iterators.',
         'How would immediate cancellation differ from snapshot semantics?', [
             ('SUB a t off b', None), ('SUB b t record x', None),
             ('PUB t one', {'callbacks': ['a:ok', 'b:ok'], 'events': ['a:one', 'b:one']}),
             ('PUB t two', {'callbacks': ['a:ok'], 'events': ['a:two']}), ('STATE', ['a'])]),
    case('bus', 'New subscriptions wait until the next publish',
         'The first dispatch copies only a. The next dispatch includes c; a then tries to add c again, fails, and delivery still reaches c.',
         'Growing the live callback list during iteration can make one publish unbounded.',
         'Should repeated registration replace a handler or report a conflict?', [
             ('SUB a t add c', None), ('PUB t one', {'callbacks': ['a:ok'], 'events': ['a:one']}),
             ('PUB t two', {'callbacks': ['a:error', 'c:ok'], 'events': ['a:two', 'c:two']}), ('STATE', ['a', 'c'])]),
    case('bus', 'Recursive publish is isolated and the guard resets',
         'A callback attempting synchronous recursion receives a rejection. The outer dispatch records its failure, runs b, and remains usable afterwards.',
         'A manually reset boolean can remain set after an unexpected exception.',
         'How would a queued event loop support recursive emission safely?', [
             ('SUB a t recursive x', None), ('SUB b t record x', None),
             ('PUB t one', {'callbacks': ['a:error', 'b:ok'], 'events': ['a:one', 'b:one']}),
             ('PUB t two', {'callbacks': ['a:error', 'b:ok'], 'events': ['a:two', 'b:two']})]),
    case('scheduler', 'Time, priority, then insertion order',
         'Earlier due times win before priority is considered. Equal due times use higher priority, then stable insertion sequence.',
         'A priority-only heap can run a future task before a due task.',
         'Why does a comparator need a strict weak ordering?', [
             ('ADD low 5 1 ok', None), ('ADD high 5 9 ok', None), ('ADD tie 5 9 ok', None),
             ('ADD early 4 0 ok', None), ('ADVANCE 5', ['early:succeeded', 'high:succeeded', 'tie:succeeded', 'low:succeeded'])]),
    case('scheduler', 'Cancelled heap entries are skipped',
         'Cancellation changes authoritative state without searching the heap. A popped tombstone is discarded and the ID remains reserved.',
         'Reusing an ID without generation numbers can revive an obsolete heap entry.',
         'When would heap compaction become necessary?', [
             ('ADD a 2 0 ok', None), ('CANCEL a', True), ('CANCEL a', False), ('ADVANCE 2', []),
             ('ADD a 3 0 ok', error('duplicate task')), ('STATE', {'a': 'cancelled'})]),
    case('scheduler', 'A throwing action does not block later tasks',
         'The runner supplies an action that really throws. The scheduler records failed and continues draining due work, without rerunning completed actions.',
         'Marking a task successful before invoking it hides execution failure.',
         'What new states and attempt IDs would retries require?', [
             ('ADD bad 1 0 fail', None), ('ADD good 1 0 ok', None),
             ('ADVANCE 1', ['bad:failed', 'good:succeeded']), ('ADVANCE 1', []),
             ('STATE', {'bad': 'failed', 'good': 'succeeded'})]),
    case('scheduler', 'Time validation precedes queue mutation',
         'After advancing to 10, a task due at 9 is invalid. A valid task due at the current time runs on the next explicit ADVANCE.',
         'Executing immediately inside ADD creates inconsistent reentrancy semantics.',
         'How does a real worker wake when a new earliest task is inserted?', [
             ('ADVANCE 10', []), ('ADD past 9 0 ok', error('task in past')),
             ('ADVANCE 9', error('time regressed')), ('ADD now 10 0 ok', None), ('ADVANCE 10', ['now:succeeded'])]),
    case('vending', 'Bounded exact change defeats a greedy choice',
         'Tea costs 4 and an inserted 10 needs 6 change. Available 4 and two 3 coins cannot satisfy a greedy 4-first path, but 3+3 is feasible.',
         'Canonical currency assumptions do not hold for arbitrary denominations and limited stock.',
         'Does this contract require any feasible change or minimum-coin change?', [
             ('SELECT tea', None), ('INSERT 10', None), ('VEND', [3, 3]),
             ('STATE', {'stock': {'snack': 1, 'tea': 1}, 'cash': 14, 'credit': 0, 'selected': None})]),
    case('vending', 'Impossible change leaves the whole session intact',
         'Two inserted 3 coins provide credit 6 for tea, but no available subset makes change 2. Failure retains both escrow coins and stock.',
         'Deducting stock before checking change can lose inventory on a rejected sale.',
         'Where would you place the commit point with a physical dispenser?', [
             ('SELECT tea', None), ('INSERT 3', None), ('INSERT 3', None), ('VEND', error('exact change unavailable')),
             ('STATE', {'stock': {'snack': 1, 'tea': 2}, 'cash': 10, 'credit': 6, 'selected': 'tea'}), ('CANCEL', [3, 3])]),
    case('vending', 'Cancel refunds only customer escrow',
         'Cancellation returns the inserted denominations, leaves machine cash unchanged and clears the selected item. A repeated cancel is an empty refund.',
         'Refunding from total machine cash allows the session to withdraw unrelated money.',
         'How do payment IDs make cancellation idempotent across retries?', [
             ('SELECT snack', None), ('INSERT 4', None), ('INSERT 1', None), ('CANCEL', [1, 4]), ('CANCEL', []),
             ('STATE', {'stock': {'snack': 1, 'tea': 2}, 'cash': 10, 'credit': 0, 'selected': None})]),
    case('vending', 'Validation, insufficient funds and stockout',
         'Unsupported coins and underpayment do not mutate inventory. Two exact-price sales consume the two teas; selecting a third tea fails.',
         'A purchase button must recheck availability even after selection.',
         'What changes if several sessions can select the last item?', [
             ('SELECT tea', None), ('INSERT 2', error('unsupported coin')), ('VEND', error('insufficient credit')),
             ('INSERT 4', None), ('VEND', []), ('SELECT tea', None), ('INSERT 4', None), ('VEND', []),
             ('SELECT tea', error('out of stock'))]),
    case('booking', 'Adjacent meetings share a room',
         'Intervals are half-open. A meeting ending at 20 does not overlap one starting at 20, and best fit chooses room A for both.',
         'Using <= for both overlap comparisons rejects adjacency.',
         'Where would a cleanup buffer enter the interval model?', [
             ('BOOK first 10 20 2', 'A'), ('BOOK next 20 30 2', 'A'),
             ('BOOK overlap 19 21 2', 'B'), ('STATE', {'first': ['A', 10, 20, 2], 'next': ['A', 20, 30, 2], 'overlap': ['B', 19, 21, 2]})]),
    case('booking', 'Best fit has a deterministic tie break',
         'Rooms B and C both fit four attendees. Lexicographic room ID breaks equal capacities; the third overlapping request has no room.',
         'Iterating an unordered container makes allocation order unstable.',
         'How might fairness change the allocator policy?', [
             ('BOOK x 0 10 4', 'B'), ('BOOK y 0 10 4', 'C'), ('BOOK z 0 10 4', error('no room')),
             ('CANCEL x', True), ('BOOK z 0 10 4', 'B')]),
    case('booking', 'A failed move preserves the original reservation',
         'The candidate is chosen before the existing booking is replaced. Moving x into a fully occupied four-person interval fails without freeing its old slot.',
         'Delete-then-book loses the original reservation on failure.',
         'Which database constraint can protect concurrent interval allocation?', [
             ('BOOK x 0 10 4', 'B'), ('BOOK y 10 20 4', 'B'), ('BOOK z 10 20 4', 'C'),
             ('MOVE x 10 20 4', error('no room')),
             ('STATE', {'x': ['B', 0, 10, 4], 'y': ['B', 10, 20, 4], 'z': ['C', 10, 20, 4]})]),
    case('booking', 'A move ignores its own old interval',
         'Rescheduling x over its current interval is valid because its own occupancy is excluded. Bad intervals and duplicate IDs are rejected.',
         'Treating the booking being moved as a conflict rejects harmless updates.',
         'Would an idempotent booking endpoint accept an identical duplicate?', [
             ('BOOK x 0 10 2', 'A'), ('MOVE x 2 8 2', 'A'), ('BOOK x 30 40 2', error('duplicate booking')),
             ('MOVE x 8 8 2', error('invalid interval')), ('STATE', {'x': ['A', 2, 8, 2]})]),
    case('search', 'AND, OR and deterministic ranking',
         'Query terms are distinct. Score is the sum of their document frequencies. AND requires every term; OR needs one. Equal scores sort by document ID.',
         'Counting repeated query words again changes the declared scoring contract.',
         'What does BM25 add beyond this raw-frequency score?', [
             ('PUT b "red blue"', None), ('PUT a "red red"', None), ('PUT c blue', None),
             ('FIND AND "RED blue"', [['b', 2]]), ('FIND OR "red red blue"', [['a', 2], ['b', 2], ['c', 1]])]),
    case('search', 'Replacement removes stale postings',
         'Updating a document first removes its old term postings. Old words no longer match, and erase removes the new postings too.',
         'Only adding new postings makes replacement behave like append.',
         'How would you publish an index generation atomically?', [
             ('PUT a old', None), ('PUT a new', None), ('FIND OR old', []), ('FIND AND new', [['a', 1]]),
             ('ERASE a', True), ('ERASE a', False), ('FIND OR new', [])]),
    case('search', 'Tokenization is an explicit ASCII contract',
         'Letters are lowercased, ASCII digits stay in words and punctuation splits words. The token api2 differs from api.',
         'A locale-sensitive tokenizer can produce different results across environments.',
         'What must change for multilingual search?', [
             ('PUT a "Node.js API2 api"', None), ('FIND AND "node JS"', [['a', 2]]),
             ('FIND OR API2', [['a', 1]]), ('FIND OR "!!!"', []), ('FIND AND ""', [])]),
    case('search', 'Missing terms and invalid modes',
         'A missing query term makes AND empty but does not suppress other OR matches. Invalid modes do not change stored documents.',
         'Skipping unknown terms in AND makes the query less restrictive than requested.',
         'How would access-control filtering change candidate selection?', [
             ('PUT a red', None), ('FIND AND "red missing"', []), ('FIND OR "red missing"', [['a', 1]]),
             ('FIND XOR red', error('invalid search mode')), ('FIND AND red', [['a', 1]])]),
    case('flags', 'Undefined flags fail closed; percentage endpoints are exact',
         'No config means disabled. A zero-percent policy enables nobody and a hundred-percent policy enables every valid identity.',
         'A <= threshold comparison accidentally enables one bucket at zero percent.',
         'When might a non-security feature need a configurable default?', [
             ('EVAL t new user', False), ('UPDATE t new 1 0', True), ('EVAL t new user', False),
             ('UPDATE t new 2 100', True), ('EVAL t new user', True)]),
    case('flags', 'Retries and conflicting versions differ',
         'An identical version and value is an idempotent no-op. The same version with a different percentage is a conflict; lower versions are stale.',
         'Accepting stale updates can undo an emergency disable.',
         'Can timestamps replace an authoritative version under clock skew?', [
             ('UPDATE t f 4 100', True), ('UPDATE t f 4 100', False), ('UPDATE t f 4 0', error('version conflict')),
             ('UPDATE t f 3 0', error('stale version')), ('EVAL t f u', True)]),
    case('flags', 'Tenant configurations stay separate',
         'The configuration key includes tenant and flag. Disabling a flag in one tenant cannot overwrite the policy for another tenant.',
         'Keying only by flag name breaks tenant isolation.',
         'Who is allowed to write tenant configuration?', [
             ('UPDATE alpha f 1 100', True), ('UPDATE beta f 1 0', True),
             ('EVAL alpha f u', True), ('EVAL beta f u', False), ('EVAL gamma f u', False)]),
    case('flags', 'Invalid policy changes preserve the last valid policy',
         'Percentage and version validation happen before replacement. A failed update leaves evaluation on the last valid zero-percent policy.',
         'Clamping an invalid percentage hides bad configuration input.',
         'What should a remote client do when a configuration stream disconnects?', [
             ('UPDATE t f 1 0', True), ('UPDATE t f 2 101', error('invalid percentage')),
             ('UPDATE t f 0 50', error('invalid version')), ('EVAL t f u', False), ('UPDATE t f 2 100', True), ('EVAL t f u', True)]),
]
for number, item in enumerate(CASES, 1):
    item['id'] = f'T{number:02}'
