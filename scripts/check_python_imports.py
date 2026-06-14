"""scripts/check_python_imports.py — 静态 + 动态 import 检查（C 阶段）。

- AST 扫所有 .py 文件：确保 compile 通过
- 真实 import：复用 venv site-packages + 加 root 路径，
  import main / models / schemas / 全部 service / router
- 不连接 DB（monkeypatch init_db 为 noop；不会触发 lifespan）
"""
import ast
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
API = REPO / "apps" / "api"


def ast_scan() -> int:
    files = list((API).rglob("*.py"))
    files = [f for f in files if ".venv-check" not in f.parts]
    print(f"[ast] scanning {len(files)} .py files in apps/api ...")
    for f in files:
        src = f.read_text(encoding="utf-8")
        try:
            ast.parse(src, filename=str(f))
        except SyntaxError as e:
            print(f"[FAIL] {f.relative_to(REPO)}: {e}")
            return 1
    print(f"[ok] all {len(files)} files parsed by AST")
    return 0


def import_smoke() -> int:
    code = """
import sys
from pathlib import Path
import os

# Resolve paths from CWD (subprocess is launched with cwd=apps/api).
# Layout: REPO/apps/api  ->  cwd=apps/api  ->  REPO = cwd.parent.parent
API = Path(os.getcwd()).resolve()
APPS = API.parent        # repo/apps
REPO = APPS.parent       # repo root
PACKAGES = REPO / 'packages'

# Optional local check-venv (Windows layout + Linux venv layout).
# Only added if present; never required.
VENV_CANDIDATES = [
    API / '.venv-check' / 'Lib' / 'site-packages',
    API / '.venv-check' / 'lib',
]
for candidate in VENV_CANDIDATES:
    if candidate.exists():
        s = str(candidate)
        if s not in sys.path:
            sys.path.insert(0, s)

# Make sure repo-root, apps/, apps/api and packages/ are importable.
for p in (API, APPS, REPO, PACKAGES):
    try:
        if p.exists():
            s = str(p)
            if s not in sys.path:
                sys.path.insert(0, s)
    except OSError:
        pass

print(f'[paths] REPO={REPO}')
print(f'[paths] APPS={APPS}')
print(f'[paths] API={API}')
print(f'[paths] PACKAGES={PACKAGES} (exists={PACKAGES.exists()})')
print(f'[paths] sys.path head: ' + ' | '.join(sys.path[:6]))

import database
async def _noop():
    return None
database.init_db = _noop  # type: ignore

import config, auth, models, schemas
import services.community_service
import services.topic_service
import services.thread_service
import services.relation_service
import services.follow_service
import services.signal_service
import services.plaza_service
import core.open_topic
import api.open_topic_communities
import api.open_topic_topics
import api.open_topic_threads
import api.open_topic_relations
import api.open_topic_follows
import api.open_topic_signals
import api.open_topic
import api.open_plaza
import main

# 6 个新 ORM 类
for cls in ['Community', 'Topic', 'Thread', 'TopicSummary', 'Relation', 'Follow']:
    assert hasattr(models, cls), f'models missing {cls}'
assert hasattr(models, 'Signal'), 'models missing Signal (C2-lite)'
print(f'[ok] 7 new ORM classes present: Community, Topic, Thread, TopicSummary, Relation, Follow, Signal')

# core.open_topic 常量
import core.open_topic as ot
assert len(ot.SUBJECT_TYPES) >= 8
assert 'topic' in ot.SUBJECT_TYPES
assert 'follows' in ot.RELATION_TYPES
assert 'community' in ot.FOLLOW_TARGET_TYPES
assert 'looking_for_person' in ot.SIGNAL_INTENT_TYPES
assert 'offering_help' in ot.SIGNAL_INTENT_TYPES
print(f'[ok] core.open_topic: SUBJECT_TYPES={len(ot.SUBJECT_TYPES)}, RELATION_TYPES={len(ot.RELATION_TYPES)}, FOLLOW_TARGET_TYPES={len(ot.FOLLOW_TARGET_TYPES)}, SIGNAL_INTENT_TYPES={len(ot.SIGNAL_INTENT_TYPES)}')

# /api/open-topic/* 挂载
assert any('open-topic' in (getattr(r, 'path', '') or '') for r in main.app.routes), 'open-topic prefix not mounted'
print('[ok] /api/open-topic/* mounted in main.app')

# /api/plaza 挂载（C2-lite）
assert any('plaza' in (getattr(r, 'path', '') or '') for r in main.app.routes), 'plaza prefix not mounted'
print('[ok] /api/plaza/* mounted in main.app')

# open_topic 子路由
import api.open_topic as ot_api
sub = sorted({r.path for r in ot_api.router.routes})
print(f'[ok] open_topic subroutes: {len(sub)}')
for p in sub:
    methods = sorted(r.methods - {'HEAD'} for r in ot_api.router.routes if r.path == p)
    # methods 是 set of set, 取并集
    flat = set()
    for r in ot_api.router.routes:
        if r.path == p:
            flat |= (r.methods - {'HEAD'})
    print(f'  - {p}  methods={sorted(flat)}')

# 校验旧 schema 表还在 (Tenant, User, Channel, Post, Comment, Tag, APIToken, Notification, AIProviderConfig, AIUsageLog, AuditLog)
for cls in ['Tenant', 'User', 'Channel', 'Post', 'Comment', 'Tag', 'APIToken',
            'Notification', 'AIProviderConfig', 'AIUsageLog', 'AuditLog']:
    assert hasattr(models, cls), f'OLD model {cls} missing!'
print('[ok] all 11 old model classes still present (no rename, no drop)')

# 校验 schemas.py 旧类还在
for cls in ['UserPublic', 'ChannelCreate', 'ChannelPublic', 'PostCreate', 'PostPublic',
            'CommentCreate', 'CommentPublic', 'NotificationPublic', 'AIProviderCreate', 'AdminUserAction']:
    assert hasattr(schemas, cls), f'OLD schema {cls} missing!'
print('[ok] all 10 old pydantic schemas still present (no rename)')

# 校验旧 router 还在
import api.auth, api.users, api.channels, api.posts, api.comments, api.ai, api.admin, api.export, api.notifications
print('[ok] all 9 old routers still importable (no rename, no drop)')

print('\\n[ALL PYTHON IMPORT CHECKS PASSED]')
"""
    p = API / "_import_smoke.py"
    p.write_text(code, encoding="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, str(p)],
            cwd=str(API),
            capture_output=True,
            text=True,
            timeout=60,
        )
        # Always echo child stdout so the GitHub Actions log shows progress.
        if result.stdout:
            print("--- child stdout ---")
            print(result.stdout)
        if result.returncode != 0:
            print("--- child STDERR ---")
            if result.stderr:
                print(result.stderr)
            else:
                print("(empty)")
            print(f"--- child exit code: {result.returncode} ---")
            return result.returncode
    finally:
        p.unlink(missing_ok=True)
    return 0


def main() -> int:
    rc = ast_scan()
    if rc != 0:
        return rc
    rc = import_smoke()
    if rc != 0:
        return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
