---
name: save_note
track: team
kind: action
provider: none (local file in notes/)
requires_env: []
inputs: [text, title, confirmed]
outputs: [status, path, chars]
side_effect: true
---
# save_note

Saves a text note as a Markdown file under `notes/` (git-ignored). It is a write action, so it only writes when `confirmed` is exactly the boolean `true`; anything else, including truthy strings such as `"false"`, returns `needs_confirmation` and writes nothing.

The file name is `<timestamp>_<slug>.md`, where the slug is ASCII only (built from `title`, or from the first line of `text`), so a title like `../../x` cannot escape `notes/`. An existing file is never overwritten (a counter is appended). Empty or oversized `text` (over 20000 characters) returns an error dict instead of raising.
