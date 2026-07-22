from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class GameAccount:
    id: int
    name: str
    display_name: str
    uid: str
    account_name: str
    official: bool = True
    theme_color: str = "#7457ff"

    @property
    def source(self) -> str:
        return f"bilibili_{self.uid}"

    def game_dict(self) -> dict:
        data = asdict(self)
        data.pop("uid")
        data.pop("account_name")
        data["enabled"] = True
        return data


ACCOUNTS: tuple[GameAccount, ...] = (
    GameAccount(1, "arcaea", "Arcaea", "404145357", "韵律源点Arcaea", theme_color="#7457ff"),
    GameAccount(2, "maimai_cn", "舞萌DX 国服", "481648327", "舞萌DX", theme_color="#ff9f43"),
    GameAccount(3, "maimai_jp", "maimai 日服资讯", "552507635", "舞萌でらっくす公式", False, "#ffb36b"),
    GameAccount(4, "paradigm", "范式：起源", "1388199065", "范式起源Paradigm", theme_color="#4d9dff"),
    GameAccount(5, "muse_dash", "Muse Dash", "269396974", "MuseDash_喵斯快跑", theme_color="#ff5d9e"),
    GameAccount(6, "phigros", "Phigros", "414149787", "Phigros官方", theme_color="#55c7c2"),
    GameAccount(7, "rotaeno", "Rotaeno", "103243330", "旋转音律Rotaeno", theme_color="#4c8dff"),
    GameAccount(8, "lanota", "Lanota", "1428322090", "调律诗篇官方", theme_color="#52b788"),
    GameAccount(9, "bleap", "Bleap 闪音跃动", "3461575931333240", "Bleap闪音跃动", theme_color="#ff6b6b"),
    GameAccount(10, "milthm", "Milthm", "3493293604211076", "梦见霖音Milthm", theme_color="#71a6ff"),
    GameAccount(11, "notanote", "Notanote", "701972652", "诺物语Notanote", theme_color="#c77dff"),
    GameAccount(12, "pjsk_jp", "世界计划日服资讯", "13148307", "Project_SEKAI资讯站", False, "#00c2a8"),
    GameAccount(13, "orzmic", "Orzmic", "516654019", "Orzmic官方", theme_color="#9676ff"),
    GameAccount(14, "pjsk_cn", "世界计划国服", "3546749308242173", "初音未来缤纷舞台", theme_color="#00d4c8"),
)

GAMES = [account.game_dict() for account in ACCOUNTS]
