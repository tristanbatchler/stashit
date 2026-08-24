-- name: GetStash :one
SELECT * FROM stashes WHERE ID = ?;

-- name: GetStashTextContent :one
SELECT * FROM stashes_text_content WHERE stash_id = ?;

-- name: GetStashBinaryPath :one
SELECT * FROM stashes_binary_paths WHERE stash_id = ?;


