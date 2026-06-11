#!/usr/bin/env python3
"""
scripts/apply_migration_0001.py

显式迁移脚本：手工运行，绝不在生产启动时静默自动改库。
用法：
    py scripts/apply_migration_0001.py                # 走 $DATABASE_URL
    py scripts/apply_migration_0001.py --dsn <dsn>    # 自定义
    py scripts/apply_migration_0001.py --dry-run      # 只打印 SQL，不执行

依赖（已声明在 apps/api/requirements.txt 第 9 行）：
- psycopg2-binary==2.9.10  (sync fallback for migrations，原仓库已声明)

注意：
- 旧库需要已经按 db/schema.sql 初始化（至少有 tenants / users 表）
- 本脚本使用同步 psycopg2，避免在迁移场景引入 async 依赖
- 若表已存在：CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS 幂等
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

try:
    import psycopg2  # type: ignore
except ImportError:
    print(
        "[err] psycopg2 未安装。\n"
        "      项目已声明 psycopg2-binary==2.9.10（apps/api/requirements.txt），\n"
        "      请在 apps/api 目录下 `py -m pip install -r requirements.txt`\n"
        "      或 `py -m pip install psycopg2-binary`",
        file=sys.stderr,
    )
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_FILE = REPO_ROOT / "db" / "migrations" / "0001_open_topic_network.sql"


def _normalize_dsn(dsn: str) -> str:
    """允许 async 风格的 DSN (postgresql+asyncpg://) 自动转 sync (postgresql://)"""
    if dsn.startswith("postgresql+asyncpg://"):
        return "postgresql://" + dsn[len("postgresql+asyncpg://"):]
    if dsn.startswith("postgresql+psycopg2://"):
        return "postgresql://" + dsn[len("postgresql+psycopg2://"):]
    return dsn


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply OpenCord migration 0001: Open Topic Network")
    parser.add_argument("--dsn", default=os.environ.get("DATABASE_URL"), help="PostgreSQL DSN (默认 $DATABASE_URL)")
    parser.add_argument("--dry-run", action="store_true", help="只打印 SQL，不执行")
    args = parser.parse_args()

    if not args.dsn:
        print("[err] 未提供 DSN。设置 $DATABASE_URL 或用 --dsn。", file=sys.stderr)
        return 2

    if not MIGRATION_FILE.exists():
        print(f"[err] 找不到迁移文件: {MIGRATION_FILE}", file=sys.stderr)
        return 2

    sql = MIGRATION_FILE.read_text(encoding="utf-8")
    dsn = _normalize_dsn(args.dsn)

    print(f"[info] DSN: {dsn.split('@')[-1]}")  # 不打印密码
    print(f"[info] Migration: {MIGRATION_FILE.relative_to(REPO_ROOT)}")
    print(f"[info] SQL length: {len(sql)} chars")

    if args.dry_run:
        print("----- SQL (dry-run, NOT executed) -----")
        print(sql)
        return 0

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    finally:
        conn.close()
    print("[ok] 迁移 0001 已应用")
    return 0


if __name__ == "__main__":
    sys.exit(main())
