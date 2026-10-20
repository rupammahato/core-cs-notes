# Machine Coding Practice — Part 9: In-Memory Document Search

**M7: keep document state and its derived index consistent through replacement and deletion.**

## 1. The problem and its purpose

Build a small mutable search service supporting document insertion/replacement, deletion and AND/OR text search. An inverted index maps a term to the documents containing it. It avoids scanning every document for every query, at the cost of maintaining derived state on writes.

Clarify tokenization, case, query repetition, empty queries, ranking, tie breaks and replacement. This lab accepts printable ASCII, lowercases A-Z, groups ASCII letters/digits into words and splits on all other characters. It does not stem, normalize Unicode, expand synonyms or support phrases.

## 2. Contract and data structures

| Structure | Purpose |
| --- | --- |
| documents[id][term] = frequency | Authoritative per-document term frequencies |
| index[term][id] = frequency | Derived postings for efficient candidate discovery |
| query term set | Repeated query words count once |
| result ordering | Descending sum of matched-term frequencies, then ascending ID |

AND requires every distinct query term. OR requires at least one. Empty or punctuation-only queries return no results. A missing term makes AND empty; it must not be ignored. Document IDs are nonempty. PUT replaces an existing document, including removal of all old terms. An empty document is allowed and matches nothing.

The index invariant is bidirectional: every stored document-term frequency has the same posting, and every posting refers to a stored document with that frequency. No postings map is empty after a completed update.

## 3. Build and mutation reasoning

Implement the analyzer once and reuse it for both documents and queries. Parse a replacement document completely before removing the old postings. On erase, remove the ID from each old term's postings and remove any empty postings map.

For a query, visit postings for each distinct term. Accumulate each candidate's score and number of matched query terms. Keep all OR candidates; keep an AND candidate only if its match count equals the distinct query term count. Sort with a stable declared tie rule rather than relying on container traversal.

The code validates text before replacement, which preserves the old document on an invalid-text rejection. It does not provide a verified allocation-failure transaction across the two maps. A stronger guarantee could build a complete candidate index generation and publish it by swap, with an explicit memory trade-off.

## 4. Complete model implementation

<!-- BEGIN MODEL -->

```cpp
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
```

<!-- END MODEL -->

## 5. Worked command traces

<!-- BEGIN TRACES -->

### T25. AND, OR and deterministic ranking

**Worked explanation:** Query terms are distinct. Score is the sum of their document frequencies. AND requires every term; OR needs one. Equal scores sort by document ID.

Run `python examples/machine-coding/verify.py --trace T25` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
PUT b "red blue"
{"ok":true,"result":null}
PUT a "red red"
{"ok":true,"result":null}
PUT c blue
{"ok":true,"result":null}
FIND AND "RED blue"
{"ok":true,"result":[["b",2]]}
FIND OR "red red blue"
{"ok":true,"result":[["a",2],["b",2],["c",1]]}
```

**Common trap:** Counting repeated query words again changes the declared scoring contract.

**Interview follow-up:** What does BM25 add beyond this raw-frequency score?

### T26. Replacement removes stale postings

**Worked explanation:** Updating a document first removes its old term postings. Old words no longer match, and erase removes the new postings too.

Run `python examples/machine-coding/verify.py --trace T26` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
PUT a old
{"ok":true,"result":null}
PUT a new
{"ok":true,"result":null}
FIND OR old
{"ok":true,"result":[]}
FIND AND new
{"ok":true,"result":[["a",1]]}
ERASE a
{"ok":true,"result":true}
ERASE a
{"ok":true,"result":false}
FIND OR new
{"ok":true,"result":[]}
```

**Common trap:** Only adding new postings makes replacement behave like append.

**Interview follow-up:** How would you publish an index generation atomically?

### T27. Tokenization is an explicit ASCII contract

**Worked explanation:** Letters are lowercased, ASCII digits stay in words and punctuation splits words. The token api2 differs from api.

Run `python examples/machine-coding/verify.py --trace T27` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
PUT a "Node.js API2 api"
{"ok":true,"result":null}
FIND AND "node JS"
{"ok":true,"result":[["a",2]]}
FIND OR API2
{"ok":true,"result":[["a",1]]}
FIND OR "!!!"
{"ok":true,"result":[]}
FIND AND ""
{"ok":true,"result":[]}
```

**Common trap:** A locale-sensitive tokenizer can produce different results across environments.

**Interview follow-up:** What must change for multilingual search?

### T28. Missing terms and invalid modes

**Worked explanation:** A missing query term makes AND empty but does not suppress other OR matches. Invalid modes do not change stored documents.

Run `python examples/machine-coding/verify.py --trace T28` after compiling with the verifier.

**Verified transcript** (command, then JSON response):

```text
PUT a red
{"ok":true,"result":null}
FIND AND "red missing"
{"ok":true,"result":[]}
FIND OR "red missing"
{"ok":true,"result":[["a",1]]}
FIND XOR red
{"ok":false,"error":"invalid search mode"}
FIND AND red
{"ok":true,"result":[["a",1]]}
```

**Common trap:** Skipping unknown terms in AND makes the query less restrictive than requested.

**Interview follow-up:** How would access-control filtering change candidate selection?

<!-- END TRACES -->

## 6. Complexity and ranking limits

Let L be input text length, T its distinct terms, D the document count, V the vocabulary size, P the total postings visited by a query, and K its candidate count. Building frequencies costs O(L log T) ordered-map work, ignoring word-comparison length. Updating postings adds map work for old and new terms, roughly O((T_old+T_new)(log V+log D)), plus document lookup and copying.

A query analyzes its input, looks up each distinct term and accumulates visited postings in an ordered candidate map: O(P log K), plus term lookups and O(K log K) ranking. Storage is O(total distinct document-term pairs), represented twice across the maps, plus identifiers and terms.

Raw term frequency favors repetition and long documents. It is intentionally a simple score, not a modern relevance system. Production ranking, phrase positions, language analysis and top-k retrieval need separate requirements and evaluation.

## 7. Architecture follow-up

For a larger index, consider immutable segments, versioned updates, deletion markers and background merging. Source-of-truth document version and index visibility version should be explicit, especially when a consumer sees stale results after an update.

Authorization cannot be omitted from a private-document search service: candidates, snippets and result counts can leak data. Apply the tenant and access-control contract consistently, rather than adding an unchecked tenant field to the result object. This local exercise has no users or authorization model.

Bridge to [search and autocomplete](/docs/system-design/search-autocomplete) and [multi-tenant RAG](/docs/system-design/multi-tenant-rag). Keyword retrieval and vector retrieval use different indexes, but both must handle deletion, visibility and access policy.

## 8. Interview questions with answers

### Q1. Why keep per-document term frequencies as well as postings?

Replacement and deletion need to know which postings belong to the old document. Without a reverse document view, deletion may scan the entire vocabulary or leave stale entries.

### Q2. What is the difference between AND and OR here?

AND requires all distinct analyzed terms, while OR requires any. Ranking then sums matched term frequencies; the boolean eligibility rule and ranking rule are separate decisions.

### Q3. Why deduplicate query terms?

The agreed query means a set of required or optional words. Repeating red does not create a second condition or extra score weight. Weighted queries would be a different contract.

### Q4. What happens to old terms after PUT replaces a document?

They are removed from the old postings before new frequencies are inserted. Otherwise searching an obsolete word would still return the updated document.

### Q5. Why is punctuation-only AND not true for every document?

The API explicitly returns no results for an empty analyzed query. Although empty-set containment could be treated as vacuously true mathematically, user-facing query semantics are a design choice.

### Q6. What does the independent oracle do?

It stores original text and scans all documents with a Python regex analyzer, then computes eligibility and score directly. It does not reproduce the C++ inverted-index update algorithm.

### Q7. Does ASCII lowercasing support multilingual text?

No. Unicode normalization, segmentation and case folding need a defined language-aware analyzer and matching query/index versions. The current adapter rejects non-ASCII input instead of pretending to support it.

### Q8. Where can access-control leaks occur?

In candidate retrieval, titles, snippets, counts, cached results and embeddings, not just the final document fetch. A production design must preserve permission scope through the whole retrieval path.

## 9. Practice tasks

- [ ] Add top-k results and compare with taking the first k entries of the full ranking oracle. Preserve the ID tie break.
- [ ] Add document versions so stale replacement cannot revive deleted content. Define tombstone retention and conflicting same-version payloads.
- [ ] Add phrase search with positional postings. Give an example where AND matches but an exact phrase does not.
- [ ] Design tenant-aware indexing and cached results. State which keys include tenant and permission version; discuss authorization changes after indexing.

Next: [Feature Flag Evaluator](/docs/machine-coding/feature-flag-evaluator).
