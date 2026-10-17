CREATE ROLE fixture_app LOGIN PASSWORD 'm16-public-fixture' NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE SCHEMA lesson;
CREATE TABLE lesson.items (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_key text NOT NULL UNIQUE,
    value text NOT NULL CHECK (length(value) BETWEEN 1 AND 80)
);
GRANT USAGE ON SCHEMA lesson TO fixture_app;
GRANT SELECT, INSERT ON lesson.items TO fixture_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA lesson TO fixture_app;
