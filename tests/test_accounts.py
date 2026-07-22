from backend.accounts import ACCOUNTS, GAMES


def test_all_confirmed_accounts_are_configured() -> None:
    assert len(ACCOUNTS) == 14
    assert {account.uid for account in ACCOUNTS} == {
        "404145357", "481648327", "552507635", "1388199065",
        "269396974", "414149787", "103243330", "1428322090",
        "3461575931333240", "3493293604211076", "701972652",
        "13148307", "516654019", "3546749308242173",
    }


def test_repost_accounts_are_not_marked_official() -> None:
    unofficial = {account.uid for account in ACCOUNTS if not account.official}
    assert unofficial == {"552507635", "13148307"}
    assert len(GAMES) == len(ACCOUNTS)
