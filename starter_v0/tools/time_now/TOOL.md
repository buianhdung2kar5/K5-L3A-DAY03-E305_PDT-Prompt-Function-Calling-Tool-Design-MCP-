---
name: time_now
track: team
kind: local
provider: none (system clock, fixed UTC+7)
requires_env: []
inputs: [when]
outputs: [date, weekday, start, end, timeframe_hint]
side_effect: false
---
# time_now

Returns the current date and time in Vietnam (UTC+7) and the date range for a relative expression: `now`, `today`, `yesterday`, `this_week` (Monday to Sunday), `last_7_days`, `this_month`.

`timeframe_hint` maps the range onto the `timeframe` values of `lookup` (`day`, `week`, `month`). An unknown `when` returns an error dict instead of raising.
