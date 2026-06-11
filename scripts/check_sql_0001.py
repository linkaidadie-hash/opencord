"""scripts/check_sql_0001.py — 静态检查 0001 SQL。"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SQL = REPO / "db" / "migrations" / "0001_open_topic_network.sql"


def main() -> int:
    sql = SQL.read_text(encoding="utf-8")

    expected_tables = ["communities", "topics", "threads", "topic_summaries", "relations", "follows"]
    for t in expected_tables:
        assert f"CREATE TABLE IF NOT EXISTS {t}" in sql, f"missing CREATE TABLE for {t}"
        print(f"[ok] CREATE TABLE IF NOT EXISTS {t}")

    assert "CREATE TYPE" not in sql, "PG ENUM not allowed in C phase"
    assert " AS ENUM" not in sql, "PG ENUM not allowed in C phase"
    print("[ok] no PG ENUM")

    for t in expected_tables:
        m = re.search(rf"CREATE TABLE IF NOT EXISTS {t}\b(.*?);", sql, re.DOTALL)
        assert m, f"could not extract {t} block"
        block = m.group(1)
        assert "tenant_id" in block, f"{t}: no tenant_id"
        assert "NOT NULL" in block, f"{t}: tenant_id not NOT NULL"
        assert "REFERENCES tenants(id)" in block, f"{t}: tenant_id not FK to tenants"
        print(f"[ok] {t}.tenant_id NOT NULL REFERENCES tenants(id)")

    # SQL 注释和 dollar-quote 里可能含 ); 清洁后再算
    cleaned = re.sub(r"--[^\n]*", "", sql)
    cleaned = re.sub(r"\$\$.*?\$\$", "$$", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"'(?:[^']|'')*'", "''", cleaned)
    a, b = cleaned.count("("), cleaned.count(")")
    assert a == b, f"unbalanced (): {a} vs {b}"
    print(f"[ok] paren balanced (after cleanup): {a} pairs")

    for idx in ["idx_communities_tenant", "idx_topics_tenant", "idx_threads_tenant",
                "idx_topic_summaries_tenant", "uq_relations_edge", "uq_follows_edge"]:
        assert idx in sql, f"missing index {idx}"
        print(f"[ok] {idx}")

    assert "trigger_set_updated_at" in sql
    print("[ok] trigger_set_updated_at referenced")

    m = re.search(r"CREATE TABLE IF NOT EXISTS topic_summaries\b(.*?);", sql, re.DOTALL)
    block = m.group(1)
    assert "generated_by" in block
    assert "VARCHAR(64)" in block
    assert "DEFAULT 'system'" in block
    print("[ok] topic_summaries.generated_by VARCHAR(64) DEFAULT 'system'")

    m = re.search(r"CREATE TABLE IF NOT EXISTS follows\b(.*?);", sql, re.DOTALL)
    block = m.group(1)
    assert "target_type" in block
    for v in ["community", "topic", "project", "user"]:
        assert v in block, f"target_type allowed value {v} not in comment"
    print("[ok] follows.target_type allowed: community/topic/project/user")

    # C 阶段硬约束：不含 agent / agent_runs / agent_actions 表
    for forbidden in ["CREATE TABLE agent", "CREATE TABLE IF NOT EXISTS agent",
                      "CREATE TABLE agent_run", "CREATE TABLE agent_action"]:
        assert forbidden not in sql, f"forbidden in C phase: {forbidden}"
    print("[ok] no agents / agent_runs / agent_actions tables in migration")

    print("\n[ALL SQL CHECKS PASSED]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
