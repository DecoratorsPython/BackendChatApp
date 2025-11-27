#!/bin/sh

commit_msg_file="$1"

first_line="$(head -n 1 "$commit_msg_file" | tr -d '\r')"

first_line="$(printf '%s' "$first_line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

regex='^TASK-[0-9]{1,}[[:space:]]*-[[:space:]]*.+$'

if ! printf '%s\n' "$first_line" | grep -Eq "$regex"; then
    echo "Invalid commit message:"
    echo "  '$first_line'"
    echo
    echo "Accepted format:"
    echo "  TASK-<number> - <description>"
    echo
    echo "Examples:"
    echo "  TASK-1 - Initial commit"
    echo "  TASK-42 - Add employee validation"
    exit 1
fi

exit 0
