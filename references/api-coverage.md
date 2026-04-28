# Dida365 Open API Coverage

Official documentation source: https://developer.dida365.com/docs/openapi.md

This skill covers all documented Open API v1 endpoint groups:

## Task

- `GET /open/v1/project/{projectId}/task/{taskId}`
- `POST /open/v1/task`
- `POST /open/v1/task/{taskId}`
- `POST /open/v1/project/{projectId}/task/{taskId}/complete`
- `DELETE /open/v1/project/{projectId}/task/{taskId}`
- `POST /open/v1/task/move`
- `POST /open/v1/task/completed`
- `POST /open/v1/task/filter`

## Project

- `GET /open/v1/project`
- `GET /open/v1/project/{projectId}`
- `GET /open/v1/project/{projectId}/data`
- `POST /open/v1/project`
- `POST /open/v1/project/{projectId}`
- `DELETE /open/v1/project/{projectId}`

## Focus

- `GET /open/v1/focus/{focusId}`
- `GET /open/v1/focus`
- `DELETE /open/v1/focus/{focusId}`

## Habit

- `GET /open/v1/habit/{habitId}`
- `GET /open/v1/habit`
- `POST /open/v1/habit`
- `POST /open/v1/habit/{habitId}`
- `POST /open/v1/habit/{habitId}/checkin`
- `GET /open/v1/habit/checkins`

## Test notes

Task and Project endpoints were tested with temporary objects and cleaned up. Habit endpoints were tested with a retained test habit because the official API has no delete-habit endpoint. Focus list was tested; focus get/delete require an existing focus record, and delete is destructive.
