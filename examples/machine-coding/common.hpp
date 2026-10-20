#pragma once
#include <algorithm>
#include <charconv>
#include <cstdint>
#include <deque>
#include <functional>
#include <iostream>
#include <map>
#include <optional>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

using Number = std::int64_t;
inline void require(bool condition, const std::string& message) {
    if (!condition) throw std::invalid_argument(message);
}
inline void identifier(const std::string& id) { require(!id.empty(), "empty identifier"); }
inline void timeValue(Number n) { require(n >= 0 && n <= 1000000000000LL, "invalid time"); }
inline std::string json(const std::string& s) {
    std::string out = "\"";
    for (char c : s) { if (c == '\\' || c == '"') out += '\\'; out += c; }
    return out + "\"";
}
inline std::string json(Number n) { return std::to_string(n); }
inline std::string json(bool b) { return b ? "true" : "false"; }
inline std::string json(const std::vector<std::string>& values) {
    std::string out = "[";
    for (const auto& s : values) { if (out.size() > 1) out += ','; out += json(s); }
    return out + ']';
}
inline std::string json(const std::map<std::string, std::string>& values) {
    std::string out = "{";
    for (const auto& [k, v] : values) { if (out.size() > 1) out += ','; out += json(k) + ':' + json(v); }
    return out + '}';
}

// ASCII command format: whitespace tokens or double-quoted strings; only \\ and \" escapes.
inline std::vector<std::string> tokenize(const std::string& line) {
    require(line.size() <= 4096, "line too long");
    for (unsigned char c : line) require(c >= 32 && c <= 126, "ASCII input required");
    std::vector<std::string> out;
    std::size_t i = 0;
    while (i < line.size()) {
        if (line[i] == ' ') { ++i; continue; }
        std::string value;
        if (line[i] == '"') {
            ++i; bool closed = false;
            while (i < line.size()) {
                char c = line[i++];
                if (c == '"') { closed = true; break; }
                if (c == '\\') {
                    require(i < line.size(), "dangling escape"); c = line[i++];
                    require(c == '\\' || c == '"', "invalid escape");
                }
                value += c;
            }
            require(closed && (i == line.size() || line[i] == ' '), "malformed quote");
        } else {
            while (i < line.size() && line[i] != ' ') {
                require(line[i] != '"' && line[i] != '\\', "quote token explicitly");
                value += line[i++];
            }
        }
        out.push_back(value);
    }
    require(!out.empty(), "empty command"); return out;
}
inline Number number(const std::string& s) {
    Number n = 0;
    const auto result = std::from_chars(s.data(), s.data() + s.size(), n);
    require(result.ec == std::errc{} && result.ptr == s.data() + s.size(), "invalid integer");
    return n;
}
inline void arity(const std::vector<std::string>& t, std::size_t n) {
    require(t.size() == n, "wrong arity");
}
