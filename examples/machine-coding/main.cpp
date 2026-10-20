#include "machines.hpp"

static std::string coins(const std::vector<Number>& values) {
    std::string out = "[";
    for (Number n : values) { if (out.size() > 1) out += ','; out += json(n); }
    return out + ']';
}

int main(int argc, char** argv) {
    if (argc != 2) { std::cerr << "Usage: machines <kv|limiter|bus|scheduler|vending|booking|search|flags>\n"; return 2; }
    const std::string mode = argv[1];
    const std::set<std::string> modes{"kv", "limiter", "bus", "scheduler", "vending", "booking", "search", "flags"};
    if (modes.count(mode) == 0) { std::cerr << "Unknown exercise\n"; return 2; }
    TransactionalKV kv;
    std::optional<SlidingLimiter> limiter;
    EventBus bus;
    std::vector<std::string> events;
    VirtualScheduler scheduler;
    VendingMachine vending;
    RoomBooking booking;
    DocumentSearch search;
    FeatureFlags flags;
    std::string line;
    while (std::getline(std::cin, line)) {
        try {
            auto t = tokenize(line); const auto& op = t[0]; std::string result = "null";
            if (mode == "kv") {
                if (op == "SET") { arity(t, 3); kv.set(t[1], t[2]); }
                else if (op == "GET") { arity(t, 2); auto value = kv.get(t[1]); result = value ? json(*value) : "null"; }
                else if (op == "ERASE") { arity(t, 2); result = json(kv.erase(t[1])); }
                else if (op == "BEGIN") { arity(t, 1); kv.begin(); }
                else if (op == "COMMIT") { arity(t, 1); kv.commit(); }
                else if (op == "ROLLBACK") { arity(t, 1); kv.rollback(); }
                else if (op == "STATE") { arity(t, 1); result = "{\"data\":" + json(kv.data()) + ",\"depth\":" + json(kv.depth()) + '}'; }
                else throw std::invalid_argument("unknown command");
            } else if (mode == "limiter") {
                if (op == "INIT") {
                    arity(t, 3); require(!limiter.has_value(), "already initialized");
                    auto limit = number(t[1]); auto window = number(t[2]); limiter.emplace(limit, window);
                } else if (op == "ALLOW") {
                    arity(t, 3); require(limiter.has_value(), "initialize first");
                    auto now = number(t[2]); result = json(limiter->allow(t[1], now));
                } else throw std::invalid_argument("unknown command");
            } else if (mode == "bus") {
                if (op == "SUB") {
                    arity(t, 5); auto id = t[1], topic = t[2], behavior = t[3], target = t[4];
                    require(behavior == "record" || behavior == "throw" || behavior == "off" || behavior == "add" || behavior == "recursive", "invalid behavior");
                    identifier(target);
                    bus.subscribe(id, topic, [&, id, topic, behavior, target](const std::string& payload) {
                        events.push_back(id + ":" + payload);
                        if (behavior == "throw") throw std::runtime_error("callback failed");
                        if (behavior == "off") bus.unsubscribe(target);
                        if (behavior == "add") bus.subscribe(target, topic, [&, target](const std::string& value) { events.push_back(target + ":" + value); });
                        if (behavior == "recursive") bus.publish(topic, payload);
                    });
                } else if (op == "OFF") { arity(t, 2); result = json(bus.unsubscribe(t[1])); }
                else if (op == "PUB") {
                    arity(t, 3); events.clear(); auto callbacks = bus.publish(t[1], t[2]);
                    result = "{\"callbacks\":" + json(callbacks) + ",\"events\":" + json(events) + '}';
                } else if (op == "STATE") { arity(t, 1); result = json(bus.ids()); }
                else throw std::invalid_argument("unknown command");
            } else if (mode == "scheduler") {
                if (op == "ADD") {
                    arity(t, 5); auto due = number(t[2]), priority = number(t[3]);
                    require(t[4] == "ok" || t[4] == "fail", "invalid task action");
                    bool fail = t[4] == "fail";
                    scheduler.schedule(t[1], due, priority, [fail] { if (fail) throw std::runtime_error("task failed"); });
                } else if (op == "CANCEL") { arity(t, 2); result = json(scheduler.cancel(t[1])); }
                else if (op == "ADVANCE") { arity(t, 2); auto now = number(t[1]); result = json(scheduler.advance(now)); }
                else if (op == "STATE") { arity(t, 1); result = json(scheduler.states()); }
                else throw std::invalid_argument("unknown command");
            } else if (mode == "vending") {
                if (op == "SELECT") { arity(t, 2); vending.select(t[1]); }
                else if (op == "INSERT") { arity(t, 2); auto coin = number(t[1]); vending.insert(coin); }
                else if (op == "VEND") { arity(t, 1); result = coins(vending.vend()); }
                else if (op == "CANCEL") { arity(t, 1); result = coins(vending.cancel()); }
                else if (op == "STATE") { arity(t, 1); result = vending.state(); }
                else throw std::invalid_argument("unknown command");
            } else if (mode == "booking") {
                if (op == "BOOK" || op == "MOVE") {
                    arity(t, 5); auto start = number(t[2]), end = number(t[3]), people = number(t[4]);
                    result = json(op == "BOOK" ? booking.book(t[1], start, end, people) : booking.move(t[1], start, end, people));
                } else if (op == "CANCEL") { arity(t, 2); result = json(booking.cancel(t[1])); }
                else if (op == "STATE") { arity(t, 1); result = booking.state(); }
                else throw std::invalid_argument("unknown command");
            } else if (mode == "search") {
                if (op == "PUT") { arity(t, 3); search.put(t[1], t[2]); }
                else if (op == "ERASE") { arity(t, 2); result = json(search.erase(t[1])); }
                else if (op == "FIND") {
                    arity(t, 3); auto matches = search.search(t[1], t[2]); result = "[";
                    for (const auto& [id, score] : matches) {
                        if (result.size() > 1) result += ',';
                        result += '[' + json(id) + ',' + json(score) + ']';
                    }
                    result += ']';
                } else throw std::invalid_argument("unknown command");
            } else if (mode == "flags") {
                if (op == "UPDATE") {
                    arity(t, 5); auto version = number(t[3]), percent = number(t[4]);
                    result = json(flags.update(t[1], t[2], version, percent));
                } else if (op == "EVAL" || op == "BUCKET") {
                    arity(t, 4); identifier(t[1]); identifier(t[2]); identifier(t[3]);
                    result = op == "EVAL" ? json(flags.enabled(t[1], t[2], t[3])) : json(FeatureFlags::bucket(t[1], t[2], t[3]));
                } else throw std::invalid_argument("unknown command");
            }
            std::cout << "{\"ok\":true,\"result\":" << result << "}\n";
        } catch (const std::exception& error) {
            std::cout << "{\"ok\":false,\"error\":" << json(std::string(error.what())) << "}\n";
        }
    }
}
