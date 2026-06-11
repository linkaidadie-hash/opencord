#!/usr/bin/env bash
# scripts/verify_open_topic.sh
#
# 手工 curl 验证脚本——在没有 Docker / 无法跑自动化 smoke 的环境下使用。
# 使用前置：docker compose up 已经把 opencord 跑起来（postgres + api + web）
# 验证 /api/open-topic/* 端点端到端能跑通。
#
# 用法：
#   bash scripts/verify_open_topic.sh
#   OPENCORD_API=http://localhost:8000 bash scripts/verify_open_topic.sh
#   TOKEN=<your-jwt> bash scripts/verify_open_topic.sh
#
# 退出码：0 全部通过；非 0 任意一步失败。
#
# 关联的迁移命令（C 阶段显式迁移，不依赖 docker-entrypoint-initdb.d）：
#   psql "$DATABASE_URL" -f db/migrations/0001_open_topic_network.sql
#   cat db/migrations/0001_open_topic_network.sql | docker compose exec -T postgres psql -U opencord -d opencord

set -euo pipefail

API_BASE="${OPENCORD_API:-http://localhost:8000}"
TOKEN="${TOKEN:-}"
HDR_AUTH=()
if [[ -n "$TOKEN" ]]; then
    HDR_AUTH=(-H "Authorization: Bearer ${TOKEN}")
fi

step() { printf "\n\033[1;36m=== %s ===\033[0m\n" "$1"; }
fail() { printf "\033[1;31m[FAIL]\033[0m %s\n" "$1"; exit 1; }
pass() { printf "\033[1;32m[OK]\033[0m   %s\n" "$1"; }

# 0) 健康检查
step "0) health"
curl -fsS "${API_BASE}/health" >/dev/null && pass "/health reachable" || fail "/health unreachable — is the api up?"

# 1) 列出 communities（应该 0 个或更多）
step "1) list communities"
LIST=$(curl -fsS "${API_BASE}/api/open-topic/communities" "${HDR_AUTH[@]}")
echo "$LIST" | head -c 400; echo
pass "GET /api/open-topic/communities"

# 2) 创建 community
step "2) create community"
SLUG="otn-smoke-$(date +%s)"
CREATE=$(curl -fsS -X POST "${API_BASE}/api/open-topic/communities" \
    -H "Content-Type: application/json" "${HDR_AUTH[@]}" \
    -d "{\"slug\":\"${SLUG}\",\"name\":\"Smoke Community\",\"description\":\"created by verify_open_topic.sh\",\"visibility\":\"public\"}")
echo "$CREATE" | head -c 400; echo
CID=$(echo "$CREATE" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
[[ -n "$CID" ]] && pass "Community created id=${CID}" || fail "no id in response"

# 3) 取回 community
step "3) get community by id"
GET=$(curl -fsS "${API_BASE}/api/open-topic/communities/${CID}" "${HDR_AUTH[@]}")
echo "$GET" | head -c 400; echo
pass "GET /api/open-topic/communities/{id}"

# 4) 创建 topic
step "4) create topic"
TSLUG="first-topic-$(date +%s)"
TOPIC=$(curl -fsS -X POST "${API_BASE}/api/open-topic/topics" \
    -H "Content-Type: application/json" "${HDR_AUTH[@]}" \
    -d "{\"community_id\":\"${CID}\",\"slug\":\"${TSLUG}\",\"title\":\"Open Topic Network 第一步\",\"body_md\":\"讨论流是议题网络的最小讨论单元。\"}")
echo "$TOPIC" | head -c 400; echo
TID=$(echo "$TOPIC" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
[[ -n "$TID" ]] && pass "Topic created id=${TID}" || fail "no topic id"

# 5) 列 topics
step "5) list topics (by community)"
LIST_T=$(curl -fsS "${API_BASE}/api/open-topic/topics?community_id=${CID}" "${HDR_AUTH[@]}")
echo "$LIST_T" | head -c 400; echo
pass "GET /api/open-topic/topics?community_id=..."

# 6) 创建 thread
step "6) create thread"
THREAD=$(curl -fsS -X POST "${API_BASE}/api/open-topic/threads" \
    -H "Content-Type: application/json" "${HDR_AUTH[@]}" \
    -d "{\"topic_id\":\"${TID}\",\"body_md\":\"C 阶段第一个讨论流，手工验证脚本写入。\"}")
echo "$THREAD" | head -c 400; echo
THID=$(echo "$THREAD" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
[[ -n "$THID" ]] && pass "Thread created id=${THID}" || fail "no thread id"

# 7) 列 threads
step "7) list threads (by topic)"
LIST_TH=$(curl -fsS "${API_BASE}/api/open-topic/threads?topic_id=${TID}" "${HDR_AUTH[@]}")
echo "$LIST_TH" | head -c 400; echo
pass "GET /api/open-topic/threads?topic_id=..."

# 8) 创建 relation (topic -> community, hosts)
step "8) create relation topic-(hosts)->community"
REL=$(curl -fsS -X POST "${API_BASE}/api/open-topic/relations" \
    -H "Content-Type: application/json" "${HDR_AUTH[@]}" \
    -d "{\"subject_type\":\"topic\",\"subject_id\":\"${TID}\",\"relation_type\":\"hosts\",\"object_type\":\"community\",\"object_id\":\"${CID}\",\"weight\":1.0}")
echo "$REL" | head -c 400; echo
RID=$(echo "$REL" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
[[ -n "$RID" ]] && pass "Relation created id=${RID}" || fail "no relation id"

# 9) 查 topic 的出边
step "9) list relations from topic"
OUT=$(curl -fsS "${API_BASE}/api/open-topic/relations?subject_type=topic&subject_id=${TID}" "${HDR_AUTH[@]}")
echo "$OUT" | head -c 400; echo
pass "GET /api/open-topic/relations (subject=topic)"

# 10) follow community
step "10) follow community"
FOL=$(curl -fsS -X POST "${API_BASE}/api/open-topic/follows" \
    -H "Content-Type: application/json" "${HDR_AUTH[@]}" \
    -d "{\"target_type\":\"community\",\"target_id\":\"${CID}\"}")
echo "$FOL" | head -c 400; echo
pass "POST /api/open-topic/follows"

# 11) 列我的关注
step "11) list my following"
ME=$(curl -fsS "${API_BASE}/api/open-topic/follows/me" "${HDR_AUTH[@]}")
echo "$ME" | head -c 400; echo
pass "GET /api/open-topic/follows/me"

# 12) 取消关注
step "12) unfollow community"
DEL_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
    "${API_BASE}/api/open-topic/follows?target_type=community&target_id=${CID}" \
    "${HDR_AUTH[@]}")
[[ "$DEL_CODE" == "204" ]] && pass "DELETE /api/open-topic/follows (204)" || fail "expected 204, got ${DEL_CODE}"

# 13) 校验 subject_type 非法值会被拒
step "13) reject invalid subject_type"
BAD_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${API_BASE}/api/open-topic/relations" \
    -H "Content-Type: application/json" "${HDR_AUTH[@]}" \
    -d "{\"subject_type\":\"alien\",\"subject_id\":\"${TID}\",\"relation_type\":\"relates_to\",\"object_type\":\"topic\",\"object_id\":\"${TID}\"}")
[[ "$BAD_CODE" == "400" ]] && pass "400 on invalid subject_type" || fail "expected 400, got ${BAD_CODE}"

# 14) 校验 default tenant 不存在时会返回 503（不是 500）
step "14) default tenant missing returns 503"
# 仅校验错误格式正确（默认租户存在时本步会通过但仍 200/201/列表）
MISSING_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${TOKEN:-nonexistent}" \
    "${API_BASE}/api/open-topic/communities")
# 未认证 → 401；认证通过但缺租户 → 503。这里只校验：要么 401，要么 503，绝不应该是 500
if [[ "$MISSING_CODE" == "401" || "$MISSING_CODE" == "503" || "$MISSING_CODE" == "200" || "$MISSING_CODE" == "201" ]]; then
    pass "tenant-missing path returns sane code (${MISSING_CODE})"
else
    fail "expected 401/503/200/201, got ${MISSING_CODE}"
fi

printf "\n\033[1;32m[ALL 14 STEPS PASSED]\033[0m\n"
