#!/bin/sh

branch="$(git rev-parse --abbrev-ref HEAD | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

echo "DEBUG branch: '$branch'" >&2

regex='^(feature|fix|test)/TASK-[0-9]+(-[a-zA-Z0-9_-]+)?$'

if ! printf '%s\n' "$branch" | grep -Eq "$regex"; then
    echo "Invalid branch name: '$branch'"
    echo
    echo "Accepted formats:"
    echo "  feature/TASK-<number>"
    echo "  feature/TASK-<number>-<description>"
    echo "  fix/TASK-<number>"
    echo "  fix/TASK-<number>-<description>"
    echo "  test/TASK-<number>"
    echo "  test/TASK-<number>-<description>"
    exit 1
fi

exit 0
