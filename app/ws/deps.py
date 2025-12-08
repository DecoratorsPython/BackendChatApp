SIMULATED_USERS = {
    "11111111-1111-1111-1111-111111111111": {
        "user_id": "11111111-1111-1111-1111-111111111111",
        "username": "alice",
        "email": "alice@example.com",
    },
    "22222222-2222-2222-2222-222222222222": {
        "user_id": "22222222-2222-2222-2222-222222222222",
        "username": "bob",
        "email": "bob@example.com",
    },
    "33333333-3333-3333-3333-333333333333": {
        "user_id": "33333333-3333-3333-3333-333333333333",
        "username": "charlie",
        "email": "charlie@example.com",
    },
}

SIMULATED_FRIENDSHIPS = {
    frozenset(
        {
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
        }
    ),
    frozenset(
        {
            "11111111-1111-1111-1111-111111111111",
            "33333333-3333-3333-3333-333333333333",
        }
    ),
}


def are_friends(user_a: str, user_b: str) -> bool:
    return frozenset({str(user_a), str(user_b)}) in SIMULATED_FRIENDSHIPS
