-- name: GetStash :one
SELECT * FROM stashes WHERE ID = ?;

-- name: ListStashes :many
SELECT * FROM stashes ORDER BY added LIMIT ? OFFSET ?;

-- name: GetStashTextContent :one
SELECT * FROM stashes_text_content WHERE stash_id = ?;

-- name: GetStashBinaryPath :one
SELECT * FROM stashes_binary_paths WHERE stash_id = ?;

-- name: CreateStash :one
INSERT INTO stashes (is_binary, slug) VALUES (?, ?)
RETURNING id, is_binary, slug, added;

-- name: CreateStashTextContent :exec
INSERT INTO stashes_text_content (stash_id, content) VALUES (?, ?);

-- name: CreateStashBinaryPath :exec
INSERT INTO stashes_binary_paths (stash_id, path) VALUES (?, ?);
