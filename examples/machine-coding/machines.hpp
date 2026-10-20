#pragma once
#include "common.hpp"

// BEGIN kv
class TransactionalKV {
    std::map<std::string, std::string> data_;
    std::vector<std::map<std::string, std::string>> snapshots_;
public:
    void set(const std::string& key, const std::string& value) { identifier(key); data_[key] = value; }
    std::optional<std::string> get(const std::string& key) const {
        identifier(key); auto it = data_.find(key);
        return it == data_.end() ? std::nullopt : std::optional<std::string>(it->second);
    }
    bool erase(const std::string& key) { identifier(key); return data_.erase(key) != 0; }
    void begin() { snapshots_.push_back(data_); }
    void commit() { require(!snapshots_.empty(), "no transaction"); snapshots_.pop_back(); }
    void rollback() {
        require(!snapshots_.empty(), "no transaction");
        data_.swap(snapshots_.back()); snapshots_.pop_back();
    }
    const auto& data() const { return data_; }
    Number depth() const { return static_cast<Number>(snapshots_.size()); }
};
// END kv

// BEGIN limiter
class SlidingLimiter {
    Number limit_, window_, clock_ = 0;
    std::map<std::string, std::deque<Number>> accepted_;
public:
    SlidingLimiter(Number limit, Number window) : limit_(limit), window_(window) {
        require(limit > 0 && limit <= 1000000, "invalid limit");
        require(window > 0 && window <= 1000000000000LL, "invalid window");
    }
    bool allow(const std::string& key, Number now) {
        identifier(key); timeValue(now); require(now >= clock_, "time regressed");
        clock_ = now; auto& times = accepted_[key];
        while (!times.empty() && times.front() <= now - window_) times.pop_front();
        if (static_cast<Number>(times.size()) >= limit_) return false;
        times.push_back(now); return true;
    }
};
// END limiter

// BEGIN bus
class EventBus {
public:
    using Callback = std::function<void(const std::string&)>;
    struct Subscription { std::string id, topic; Callback callback; };
private:
    std::vector<Subscription> subscriptions_;
    bool publishing_ = false;
public:
    void subscribe(const std::string& id, const std::string& topic, Callback callback) {
        identifier(id); identifier(topic); require(static_cast<bool>(callback), "empty callback");
        require(std::none_of(subscriptions_.begin(), subscriptions_.end(),
            [&](const auto& s) { return s.id == id; }), "duplicate subscription");
        subscriptions_.push_back({id, topic, std::move(callback)});
    }
    bool unsubscribe(const std::string& id) {
        identifier(id);
        auto it = std::find_if(subscriptions_.begin(), subscriptions_.end(),
            [&](const auto& s) { return s.id == id; });
        if (it == subscriptions_.end()) return false;
        subscriptions_.erase(it); return true;
    }
    std::vector<std::string> publish(const std::string& topic, const std::string& payload) {
        identifier(topic); require(!publishing_, "recursive publish");
        // Snapshot before setting the guard: a failed copy cannot leave the guard set.
        const auto snapshot = subscriptions_;
        struct Guard { bool& flag; explicit Guard(bool& f) : flag(f) { flag = true; } ~Guard() { flag = false; } } guard(publishing_);
        std::vector<std::string> results;
        for (const auto& s : snapshot) if (s.topic == topic) {
            try { s.callback(payload); results.push_back(s.id + ":ok"); }
            catch (const std::exception&) { results.push_back(s.id + ":error"); }
            catch (...) { results.push_back(s.id + ":error"); }
        }
        return results;
    }
    std::vector<std::string> ids() const {
        std::vector<std::string> result;
        for (const auto& s : subscriptions_) result.push_back(s.id);
        return result;
    }
};
// END bus

// BEGIN scheduler
class VirtualScheduler {
    struct Task { Number due, priority, sequence; std::string id; std::function<void()> action; };
    struct Later {
        bool operator()(const Task& a, const Task& b) const {
            if (a.due != b.due) return a.due > b.due;
            if (a.priority != b.priority) return a.priority < b.priority;
            return a.sequence > b.sequence;
        }
    };
    Number now_ = 0, sequence_ = 0;
    bool running_ = false;
    std::priority_queue<Task, std::vector<Task>, Later> queue_;
    std::map<std::string, std::string> states_;
public:
    void schedule(const std::string& id, Number due, Number priority, std::function<void()> action) {
        require(!running_, "scheduler is running"); require(static_cast<bool>(action), "empty action");
        identifier(id); timeValue(due); require(due >= now_, "task in past");
        require(priority >= 0 && priority <= 1000000, "invalid priority");
        require(states_.count(id) == 0, "duplicate task");
        queue_.push({due, priority, sequence_++, id, std::move(action)}); states_[id] = "scheduled";
    }
    bool cancel(const std::string& id) {
        require(!running_, "scheduler is running");
        identifier(id); auto it = states_.find(id);
        if (it == states_.end() || it->second != "scheduled") return false;
        it->second = "cancelled"; return true;
    }
    std::vector<std::string> advance(Number now) {
        require(!running_, "scheduler is running");
        timeValue(now); require(now >= now_, "time regressed"); now_ = now;
        struct Guard { bool& flag; explicit Guard(bool& f) : flag(f) { flag = true; } ~Guard() { flag = false; } } guard(running_);
        std::vector<std::string> result;
        while (!queue_.empty() && queue_.top().due <= now) {
            auto task = queue_.top(); queue_.pop();
            if (states_.at(task.id) != "scheduled") continue;
            std::string status = "succeeded";
            try { task.action(); } catch (...) { status = "failed"; }
            states_[task.id] = status; result.push_back(task.id + ":" + status);
        }
        return result;
    }
    const auto& states() const { return states_; }
};
// END scheduler

// BEGIN vending
class VendingMachine {
    struct Item { Number price, stock; };
    const std::vector<Number> denominations_{1, 3, 4, 10};
    std::map<std::string, Item> items_{{"tea", {4, 2}}, {"snack", {7, 1}}};
    std::vector<Number> cash_{0, 2, 1, 0}, escrow_{0, 0, 0, 0};
    std::optional<std::string> selected_;
    Number credit_ = 0;
public:
    void select(const std::string& id) {
        require(items_.count(id) != 0, "unknown item");
        require(items_.at(id).stock > 0, "out of stock"); selected_ = id;
    }
    void insert(Number coin) {
        auto it = std::find(denominations_.begin(), denominations_.end(), coin);
        require(it != denominations_.end(), "unsupported coin");
        require(credit_ + coin <= 1000, "credit limit");
        ++escrow_[static_cast<std::size_t>(it - denominations_.begin())]; credit_ += coin;
    }
    std::vector<Number> vend() {
        require(selected_.has_value(), "select item first");
        auto& item = items_.at(*selected_);
        require(item.stock > 0, "out of stock"); require(credit_ >= item.price, "insufficient credit");
        const Number change = credit_ - item.price;
        auto available = cash_;
        for (std::size_t i = 0; i < cash_.size(); ++i) available[i] += escrow_[i];
        // Bounded subset-sum: each available physical coin is considered once.
        std::vector<std::optional<std::vector<Number>>> dp(static_cast<std::size_t>(change + 1));
        dp[0] = std::vector<Number>(4, 0);
        for (std::size_t i = 0; i < available.size(); ++i) {
            for (Number c = 0; c < available[i]; ++c) {
                for (Number amount = change; amount >= denominations_[i]; --amount) {
                    auto source = static_cast<std::size_t>(amount - denominations_[i]);
                    auto target = static_cast<std::size_t>(amount);
                    if (!dp[target] && dp[source]) { dp[target] = *dp[source]; ++(*dp[target])[i]; }
                }
            }
        }
        require(dp[static_cast<std::size_t>(change)].has_value(), "exact change unavailable");
        auto chosen = *dp[static_cast<std::size_t>(change)];
        std::vector<Number> returned;
        for (std::size_t i = 0; i < cash_.size(); ++i) {
            available[i] -= chosen[i];
            for (Number c = 0; c < chosen[i]; ++c) returned.push_back(denominations_[i]);
        }
        --item.stock; cash_.swap(available); escrow_.assign(4, 0); credit_ = 0; selected_.reset();
        return returned;
    }
    std::vector<Number> cancel() {
        std::vector<Number> returned;
        for (std::size_t i = 0; i < escrow_.size(); ++i)
            for (Number c = 0; c < escrow_[i]; ++c) returned.push_back(denominations_[i]);
        escrow_.assign(4, 0); credit_ = 0; selected_.reset(); return returned;
    }
    std::string state() const {
        std::string stock = "{";
        for (const auto& [id, item] : items_) {
            if (stock.size() > 1) stock += ',';
            stock += json(id) + ':' + json(item.stock);
        }
        Number balance = 0;
        for (std::size_t i = 0; i < cash_.size(); ++i) balance += cash_[i] * denominations_[i];
        return "{\"stock\":" + stock + "},\"cash\":" + json(balance) + ",\"credit\":" + json(credit_)
            + ",\"selected\":" + (selected_ ? json(*selected_) : "null") + '}';
    }
};
// END vending

// BEGIN booking
class RoomBooking {
    struct Booking { std::string room; Number start, end, people; };
    const std::map<std::string, Number> rooms_{{"A", 2}, {"B", 4}, {"C", 4}};
    std::map<std::string, Booking> bookings_;
    std::string choose(Number start, Number end, Number people, const std::string& ignore) const {
        timeValue(start); timeValue(end); require(start < end, "invalid interval");
        require(people > 0 && people <= 1000000, "invalid attendees");
        std::vector<std::pair<Number, std::string>> choices;
        for (const auto& [room, capacity] : rooms_) {
            bool free = capacity >= people;
            for (const auto& [id, b] : bookings_)
                if (id != ignore && b.room == room && start < b.end && b.start < end) free = false;
            if (free) choices.push_back({capacity, room});
        }
        require(!choices.empty(), "no room"); return std::min_element(choices.begin(), choices.end())->second;
    }
public:
    std::string book(const std::string& id, Number start, Number end, Number people) {
        identifier(id); require(bookings_.count(id) == 0, "duplicate booking");
        auto room = choose(start, end, people, ""); bookings_[id] = {room, start, end, people}; return room;
    }
    std::string move(const std::string& id, Number start, Number end, Number people) {
        identifier(id); require(bookings_.count(id) != 0, "unknown booking");
        auto room = choose(start, end, people, id); bookings_[id] = {room, start, end, people}; return room;
    }
    bool cancel(const std::string& id) { identifier(id); return bookings_.erase(id) != 0; }
    std::string state() const {
        std::string out = "{";
        for (const auto& [id, b] : bookings_) {
            if (out.size() > 1) out += ',';
            out += json(id) + ":[" + json(b.room) + ',' + json(b.start) + ',' + json(b.end) + ',' + json(b.people) + ']';
        }
        return out + '}';
    }
};
// END booking

// BEGIN search
class DocumentSearch {
    using Frequencies = std::map<std::string, Number>;
    std::map<std::string, Frequencies> documents_;
    std::map<std::string, std::map<std::string, Number>> index_;
    static Frequencies terms(const std::string& text) {
        Frequencies frequencies; std::string word;
        auto flush = [&] { if (!word.empty()) { ++frequencies[word]; word.clear(); } };
        for (unsigned char c : text) {
            require(c >= 32 && c <= 126, "ASCII text required");
            if (c >= 'A' && c <= 'Z') c = static_cast<unsigned char>(c - 'A' + 'a');
            if ((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')) word += static_cast<char>(c);
            else flush();
        }
        flush(); return frequencies;
    }
public:
    bool erase(const std::string& id) {
        identifier(id); auto it = documents_.find(id); if (it == documents_.end()) return false;
        for (const auto& [term, count] : it->second) {
            (void)count; auto& postings = index_.at(term); postings.erase(id);
            if (postings.empty()) index_.erase(term);
        }
        documents_.erase(it); return true;
    }
    void put(const std::string& id, const std::string& text) {
        identifier(id); auto frequencies = terms(text); erase(id);
        documents_[id] = frequencies;
        for (const auto& [term, count] : frequencies) index_[term][id] = count;
    }
    std::vector<std::pair<std::string, Number>> search(const std::string& mode, const std::string& query) const {
        require(mode == "AND" || mode == "OR", "invalid search mode"); auto queryTerms = terms(query);
        std::map<std::string, std::pair<Number, Number>> totals;
        for (const auto& [term, ignored] : queryTerms) {
            (void)ignored; auto it = index_.find(term); if (it == index_.end()) continue;
            for (const auto& [id, frequency] : it->second) {
                totals[id].first += frequency; ++totals[id].second;
            }
        }
        std::vector<std::pair<std::string, Number>> result;
        for (const auto& [id, counts] : totals)
            if (mode == "OR" || counts.second == static_cast<Number>(queryTerms.size())) result.push_back({id, counts.first});
        std::sort(result.begin(), result.end(), [](const auto& a, const auto& b) {
            return a.second != b.second ? a.second > b.second : a.first < b.first;
        });
        return result;
    }
};
// END search

// BEGIN flags
class FeatureFlags {
    struct Config { Number version, percent; };
    std::map<std::pair<std::string, std::string>, Config> configs_;
public:
    static Number bucket(const std::string& tenant, const std::string& flag, const std::string& user) {
        // Length-prefix every component so (ab,c) cannot collide merely by concatenation with (a,bc).
        std::string input;
        for (const auto& value : {tenant, flag, user}) input += std::to_string(value.size()) + ':' + value;
        std::uint32_t hash = 2166136261u;
        for (unsigned char c : input) { hash ^= c; hash *= 16777619u; }
        return static_cast<Number>(hash % 10000u);
    }
    bool update(const std::string& tenant, const std::string& flag, Number version, Number percent) {
        identifier(tenant); identifier(flag); require(version > 0, "invalid version");
        require(percent >= 0 && percent <= 100, "invalid percentage");
        auto key = std::make_pair(tenant, flag); auto it = configs_.find(key);
        if (it != configs_.end()) {
            require(version >= it->second.version, "stale version");
            if (version == it->second.version) {
                require(percent == it->second.percent, "version conflict"); return false;
            }
        }
        configs_[key] = {version, percent}; return true;
    }
    bool enabled(const std::string& tenant, const std::string& flag, const std::string& user) const {
        identifier(tenant); identifier(flag); identifier(user);
        auto it = configs_.find({tenant, flag});
        return it != configs_.end() && bucket(tenant, flag, user) < it->second.percent * 100;
    }
};
// END flags
