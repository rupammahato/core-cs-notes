#include "machines.hpp"

int main() {
    Number checks = 0;
    auto check = [&](bool condition) { require(condition, "API test failed"); ++checks; };
    auto rejected = [&](auto action) {
        bool caught = false;
        try { action(); } catch (const std::invalid_argument&) { caught = true; }
        check(caught);
    };
    EventBus bus;
    rejected([&] { bus.subscribe("empty", "topic", {}); });
    Number calls = 0;
    bus.subscribe("first", "topic", [&](const auto&) { ++calls; bus.unsubscribe("second"); });
    bus.subscribe("second", "topic", [&](const auto&) { ++calls; throw 42; });
    check(bus.publish("topic", "x") == std::vector<std::string>{"first:ok", "second:error"});
    check(calls == 2);
    check(bus.publish("topic", "x") == std::vector<std::string>{"first:ok"});
    bus.subscribe("recursive", "topic", [&](const auto& value) { bus.publish("topic", value); });
    check(bus.publish("topic", "x") == std::vector<std::string>{"first:ok", "recursive:error"});
    check(bus.publish("topic", "x") == std::vector<std::string>{"first:ok", "recursive:error"});

    VirtualScheduler scheduler;
    rejected([&] { scheduler.schedule("empty", 0, 0, {}); });
    scheduler.schedule("modify", 2, 0, [&] { scheduler.schedule("new", 2, 0, [] {}); });
    scheduler.schedule("throw", 2, 0, [] { throw 42; });
    scheduler.schedule("record", 2, 0, [&] { ++calls; });
    check(scheduler.advance(2) == std::vector<std::string>{"modify:failed", "throw:failed", "record:succeeded"});
    check(calls == 6);
    scheduler.schedule("later", 3, 0, [&] { scheduler.cancel("later"); });
    check(scheduler.advance(3) == std::vector<std::string>{"later:failed"});
    scheduler.schedule("reenter", 4, 0, [&] { scheduler.advance(4); });
    check(scheduler.advance(4) == std::vector<std::string>{"reenter:failed"});
    check(scheduler.advance(4).empty());

    DocumentSearch index;
    index.put("doc", "old");
    rejected([&] { index.put("doc", std::string(1, '\x01')); });
    check(index.search("AND", "old") == std::vector<std::pair<std::string, Number>>{{"doc", 1}});
    std::cout << "{\"passed\":" << checks << "}\n";
}
