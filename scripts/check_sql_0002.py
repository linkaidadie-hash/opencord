"""scripts/check_sql_0002.py — 静态检查 0002 SQL (Open Plaza Signals)."""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SQL = REPO / "db" / "migrations" / "0002_open_plaza_signals.sql"


def main() -> int:
    sql = SQL.read_text(encoding="utf-8")

    # 1) 必须包含 1 张新表
    assert "CREATE TABLE IF NOT EXISTS signals" in sql, "missing CREATE TABLE for signals"
    print("[ok] CREATE TABLE IF NOT EXISTS signals")

    # 2) 不许出现 PG ENUM
    assert "CREATE TYPE" not in sql, "PG ENUM not allowed"
    assert " AS ENUM" not in sql, "PG ENUM not allowed"
    print("[ok] no PG ENUM")

    # 3) signals.tenant_id NOT NULL REFERENCES tenants
    m = re.search(r"CREATE TABLE IF NOT EXISTS signals\b(.*?);", sql, re.DOTALL)
    assert m, "could not extract signals block"
    block = m.group(1)
    assert "tenant_id" in block, "signals: no tenant_id"
    assert "NOT NULL" in block, "signals: tenant_id not NOT NULL"
    assert "REFERENCES tenants(id)" in block, "signals: tenant_id not FK to tenants"
    print("[ok] signals.tenant_id NOT NULL REFERENCES tenants(id)")

    # 4) 关键字段存在
    for col in ["user_id", "intent_type", "title", "tags", "visibility", "created_at", "updated_at"]:
        assert col in block, f"signals: missing column {col}"
    assert "topic_id" in block, "signals: missing topic_id (nullable)"
    print("[ok] signals has user_id/intent_type/title/tags/visibility/created_at/updated_at/topic_id")

    # 5) tags 是 JSONB
    assert re.search(r"tags\s+JSONB", block), "signals.tags should be JSONB"
    print("[ok] signals.tags is JSONB")

    # 6) intent_type / visibility 是 VARCHAR（非 ENUM）
    assert re.search(r"intent_type\s+VARCHAR\(\d+\)", block), "signals.intent_type should be VARCHAR"
    assert re.search(r"visibility\s+VARCHAR\(\d+\)", block), "signals.visibility should be VARCHAR"
    print("[ok] signals.intent_type + signals.visibility are VARCHAR")

    # 7) 关键索引
    for idx in ["idx_signals_tenant_recent", "idx_signals_topic", "idx_signals_user", "idx_signals_intent"]:
        assert idx in sql, f"missing index {idx}"
        print(f"[ok] {idx}")

    # 8) 触发器复用
    assert "trigger_set_updated_at" in sql
    print("[ok] trigger_set_updated_at referenced")

    # 9) 括号清洁
    cleaned = re.sub(r"--[^\n]*", "", sql)
    cleaned = re.sub(r"\$\$.*?\$\$", "$$", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"'(?:[^']|'')*'", "''", cleaned)
    a, b = cleaned.count("("), cleaned.count(")")
    assert a == b, f"unbalanced (): {a} vs {b}"
    print(f"[ok] paren balanced (after cleanup): {a} pairs")

    # 10) C2-lite 硬约束：不含 agent / encounter / project 表
    for forbidden in ["CREATE TABLE agent", "CREATE TABLE encounter",
                      "CREATE TABLE project", "CREATE TABLE task"]:
        assert forbidden not in sql, f"forbidden in C2-lite: {forbidden}"
    print("[ok] no agent / encounter / project / task tables in migration")

    print("\n[ALL SQL 0002 CHECKS PASSED]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
