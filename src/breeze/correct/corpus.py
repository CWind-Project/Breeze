"""内置小型英文词库(stdlib-only),用于匹配/排序/回归测试。"""

WORDS = [
    "verbose", "system", "computer", "network", "algorithm", "keyboard", "python",
    "library", "function", "variable", "string", "number", "object", "class",
    "method", "return", "import", "module", "package", "document", "content",
    "service", "process", "program", "running", "handler", "request", "session",
    "account", "customer", "product", "payment", "receipt", "invoice", "address",
    "country", "city", "street", "window", "button", "screen", "device", "driver",
    "printer", "monitor", "storage", "buffer", "packet", "header", "payload",
    "server", "client", "browser", "engine", "kernel", "memory", "register",
    "cache", "router", "switch", "socket", "thread", "signal", "token", "secret",
    "password", "username", "email", "phone", "mobile", "tablet", "laptop",
    "desktop", "notebook", "database", "record", "column", "table", "schema",
    "index", "query", "filter", "sorter", "search", "result", "score", "weight",
    "vector", "matrix", "tensor", "scalar", "random", "sample", "data", "model",
    "feature", "target", "source", "branch", "commit", "upload", "update",
    "insert", "delete", "modify", "create", "remove", "handle", "manage",
    "control", "execute", "compile", "deploy", "release", "version", "binary",
    "runtime", "syntax", "semantic", "literal", "keyword", "comment", "script",
    "markup", "format", "render", "layout", "border", "margin", "padding",
    "colors", "styles", "module", "object", "static", "dynamic", "public",
    "private", "hidden", "visible", "active", "offline", "online", "enable",
    "disable", "status", "record", "report", "detail", "option", "choice",
    "button", "toggle", "slider", "picker", "wizard", "canvas", "editor",
    "reader", "writer", "parser", "tester", "logger", "marker", "folder",
    "binary", "buffer", "cipher", "digest", "locale", "vendor", "device",
]


def vocabulary() -> list[str]:
    return list(dict.fromkeys(WORDS))  # 去重保序
