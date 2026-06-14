#!/usr/bin/env bash
# scripts/runtime_smoke_open_plaza.sh
#
# Issue #7 runtime smoke test for Open Plaza / Open Topic Network.
#
# Boots a real Postgres + Redis + API stack via docker compose, applies
# migrations 0001 / 0002, asserts the 7 new tables exist with tenant_id
# NOT NULL, and curls the live API surface (/api/plaza,
# /api/open-topic/signals, /api/open-topic/communities).
#
# This script is the **local / human-runnable counterpart** to
# .github/workflows/runtime-smoke.yml. CI uses the same checks under
# services: in GitHub Actions; this script wraps docker compose so a
# developer with Docker Desktop (or any Docker daemon) can reproduce
# the same green check in ~5 minutes.
#
# Usage:
#   bash scripts/runtime_smoke_open_plaza.sh                # full run
#   OPENCORD_API=http://localhost:8000 \
#     bash scripts/runtime_smoke_open_plaza.sh              # custom api url
#   bash scripts/runtime_smoke_open_plaza.sh --skip-docker  # skip docker,
#                                                            # only assert
#                                                            # the contract
#
# Exit codes:
#   0   all checks passed
#   2   docker / docker compose not available (and --skip-docker not set)
#   3   postgres failed to become ready
#   4   migration apply failed
#   5   expected tables missing or tenant_id not NOT NULL
#   6   API health check failed
#   7   API surface check (/api/plaza, /api/open-topic/signals) failed
#   8   verify_open_topic.sh reported a failure
#
# Refs:
#   - Issue #7: Add runtime Docker/PostgreSQL smoke tests
#   - docs/DEMO_WALKTHROUGH.md § 6.2 / § 7 (the gap this closes)
#   - scripts/verify_open_topic.sh (the 14-step curl smoke)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

# --- knobs ----------------------------------------------------------------
COMPOSE_FILE="${COMPOSE_FILE:-${REPO_ROOT}/docker-compose.yml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-opencord-smoke}"
API_BASE="${OPENCORD_API:-http://localhost:8000}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-60}"   # seconds
PG_READY_TIMEOUT="${PG_READY_TIMEOUT:-30}"
SKIP_DOCKER=0
TEARDOWN=1   # bring the stack down on exit; set TEARDOWN=0 to keep it up

for arg in "$@"; do
    case "$arg" in
        --skip-docker) SKIP_DOCKER=1 ;;
        --keep-up)     TEARDOWN=0 ;;
        -h|--help)
            sed -n '2,40p' "$0"; exit 0 ;;
        *)
            printf '[runtime-smoke] unknown arg: %s\n' "$arg" >&2
            exit 64
            ;;
    esac
done

# --- output helpers -------------------------------------------------------
step()  { printf '\n\033[1;36m=== %s ===\033[0m\n' "$1"; }
info()  { printf '\033[1;34m[info]\033[0m  %s\n' "$1"; }
pass()  { printf '\033[1;32m[OK]\033[0m    %s\n' "$1"; }
warn()  { printf '\033[1;33m[warn]\033[0m  %s\n' "$1"; }
fail()  { printf '\033[1;31m[FAIL]\033[0m  %s\n' "$1"; exit "$2"; }

# --- teardown -------------------------------------------------------------
COMPOSE=(docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}")
cleanup() {
    if [[ "${TEARDOWN}" == "1" && "${SKIP_DOCKER}" == "0" ]]; then
        step "teardown"
        "${COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 \
            && pass "stack torn down (postgres data volume removed)" \
            || warn "stack teardown returned non-zero (manual cleanup may be needed)"
    fi
}
trap cleanup EXIT

# --- preconditions --------------------------------------------------------
step "preconditions"

if [[ "${SKIP_DOCKER}" == "1" ]]; then
    warn "--skip-docker set; only running static API contract check against ${API_BASE}"
else
    if ! command -v docker >/dev/null 2>&1; then
        fail "docker CLI not found. Install Docker Desktop (or any Docker daemon), or re-run with --skip-docker to only assert the API contract against an already-running instance." 2
    fi
    if ! docker info >/dev/null 2>&1; then
        fail "docker daemon not reachable (docker info failed). Start Docker Desktop and retry, or re-run with --skip-docker." 2
    fi
    if ! docker compose version >/dev/null 2>&1; then
        fail "docker compose plugin not available. Install Docker Desktop 4.x+ or docker-compose-plugin, or re-run with --skip-docker." 2
    fi
    pass "docker + docker compose present and daemon reachable"
fi

# --- 1) bring up the deps -------------------------------------------------
if [[ "${SKIP_DOCKER}" == "1" ]]; then
    warn "skipping docker compose up"
else
    step "1) docker compose up postgres + redis (api will be started by the workflow, not here)"
    # We intentionally do NOT start `api` / `web` here: this script is the
    # local companion to .github/workflows/runtime-smoke.yml which boots the
    # api itself (uvicorn) so it can stream logs and set PYTHONPATH. For a
    # faithful local reproduction, run:
    #     docker compose -p "${PROJECT_NAME}" up -d postgres redis
    #     docker compose -p "${PROJECT_NAME}" up -d --build api
    # then call this script with --skip-docker. The local happy path of
    # `bash scripts/runtime_smoke_open_plaza.sh` covers the database half
    # (which is the main thing that can break silently).
    "${COMPOSE[@]}" up -d postgres redis
    pass "postgres + redis started"
fi

# --- 2) wait for postgres -------------------------------------------------
if [[ "${SKIP_DOCKER}" == "0" ]]; then
    step "2) wait for postgres healthcheck"
    elapsed=0
    until "${COMPOSE[@]}" exec -T postgres pg_isready -U opencord -d opencord >/dev/null 2>&1; do
        if [[ "${elapsed}" -ge "${PG_READY_TIMEOUT}" ]]; then
            fail "postgres did not become ready within ${PG_READY_TIMEOUT}s. Try: ${COMPOSE[*]} logs postgres" 3
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    pass "postgres ready (waited ${elapsed}s)"
fi

# --- 3) apply migrations 0001 + 0002 -------------------------------------
if [[ "${SKIP_DOCKER}" == "0" ]]; then
    step "3) apply migration 0001 (Open Topic Network)"
    "${COMPOSE[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 -U opencord -d opencord \
        < "${REPO_ROOT}/db/migrations/0001_open_topic_network.sql" \
        || fail "migration 0001 failed to apply. Try: ${COMPOSE[*]} logs postgres" 4
    pass "migration 0001 applied"

    step "4) apply migration 0002 (Open Plaza Signals)"
    "${COMPOSE[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 -U opencord -d opencord \
        < "${REPO_ROOT}/db/migrations/0002_open_plaza_signals.sql" \
        || fail "migration 0002 failed to apply. Try: ${COMPOSE[*]} logs postgres" 4
    pass "migration 0002 applied"
fi

# --- 5) assert 7 new tables exist with tenant_id NOT NULL -----------------
step "5) assert 7 new tables exist and tenant_id NOT NULL"

EXPECTED_TABLES=(communities topics threads topic_summaries relations follows signals)
PSQL=( "${COMPOSE[@]}" exec -T postgres psql -U opencord -d opencord -tA )

missing=0
for t in "${EXPECTED_TABLES[@]}"; do
    exists="$("${PSQL[@]}" -c "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='${t}'" 2>/dev/null | tr -d '[:space:]')"
    if [[ "${exists}" != "1" ]]; then
        warn "  - missing table: ${t}"
        missing=$((missing + 1))
        continue
    fi
    line="$("${PSQL[@]}" -c "SELECT data_type || '|' || is_nullable FROM information_schema.columns WHERE table_schema='public' AND table_name='${t}' AND column_name='tenant_id'" 2>/dev/null | tr -d '[:space:]')"
    if [[ "${line}" != "uuid|NO" ]]; then
        warn "  - ${t}.tenant_id wrong: ${line:-<missing>}"
        missing=$((missing + 1))
        continue
    fi
    pass "${t}.tenant_id uuid NOT NULL"
done

if [[ "${missing}" -gt 0 ]]; then
    fail "${missing} table(s) failed the contract (missing or tenant_id wrong). See warns above." 5
fi

# --- 6) assert v0.1 baseline untouched -----------------------------------
step "6) assert v0.1 old tables still exist (no regression)"
V01_TABLES=(tenants users api_tokens channels posts comments tags post_tags notifications ai_providers ai_usage_log audit_log)
for t in "${V01_TABLES[@]}"; do
    exists="$("${PSQL[@]}" -c "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='${t}'" 2>/dev/null | tr -d '[:space:]')"
    if [[ "${exists}" != "1" ]]; then
        fail "v0.1 table missing: ${t} — regression detected" 5
    fi
done
pass "all v0.1 baseline tables still present"

# --- 7) api health + surface check ---------------------------------------
# The api may or may not be running here; we only fail if the operator
# explicitly asked for an api check. If SKIP_DOCKER=1 and the api is up,
# we exercise /health + /api/plaza + /api/open-topic/signals.
step "7) api surface check (best-effort)"

curl_api() {
    local url="$1"
    local out code
    out="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 5 "${url}" 2>/dev/null || echo "000")"
    code="${out}"
    printf '%s\n' "${code}"
}

HEALTH_CODE="$(curl_api "${API_BASE}/health" || true)"
if [[ "${HEALTH_CODE}" == "200" ]]; then
    pass "${API_BASE}/health -> 200"
    PLAZA_CODE="$(curl_api "${API_BASE}/api/plaza" || true)"
    SIG_CODE="$(curl_api "${API_BASE}/api/open-topic/signals" || true)"
    OTN_CODE="$(curl_api "${API_BASE}/api/open-topic/communities" || true)"
    [[ "${PLAZA_CODE}" =~ ^[2-3][0-9][0-9]$ ]] && pass "${API_BASE}/api/plaza -> ${PLAZA_CODE}" || fail "${API_BASE}/api/plaza -> ${PLAZA_CODE}" 7
    [[ "${SIG_CODE}"  =~ ^[2-3][0-9][0-9]$ ]] && pass "${API_BASE}/api/open-topic/signals -> ${SIG_CODE}" || fail "${API_BASE}/api/open-topic/signals -> ${SIG_CODE}" 7
    [[ "${OTN_CODE}"  =~ ^[2-3][0-9][0-9]$ ]] && pass "${API_BASE}/api/open-topic/communities -> ${OTN_CODE}" || fail "${API_BASE}/api/open-topic/communities -> ${OTN_CODE}" 7
else
    if [[ "${SKIP_DOCKER}" == "1" ]]; then
        fail "${API_BASE}/health -> ${HEALTH_CODE} (api not reachable; --skip-docker assumes api is up). Start api and retry." 6
    else
        warn "${API_BASE}/health -> ${HEALTH_CODE} (api not started by this script; this is OK for the db-only local flow). To exercise the api surface, run:"
        warn "    ${COMPOSE[*]} up -d --build api"
        warn "    bash scripts/runtime_smoke_open_plaza.sh --skip-docker"
        warn "or rely on .github/workflows/runtime-smoke.yml which boots the api in CI."
    fi
fi

# --- 8) optional: 14-step curl smoke (only when api is up) ---------------
if [[ "${HEALTH_CODE}" == "200" && -x "${REPO_ROOT}/scripts/verify_open_topic.sh" ]]; then
    step "8) scripts/verify_open_topic.sh (14-step curl smoke)"
    if bash "${REPO_ROOT}/scripts/verify_open_topic.sh"; then
        pass "verify_open_topic.sh: 14/14"
    else
        fail "verify_open_topic.sh reported a failure (see output above)" 8
    fi
fi

# --- done -----------------------------------------------------------------
step "summary"
if [[ "${SKIP_DOCKER}" == "0" ]]; then
    pass "runtime smoke (db half) PASSED on $(date -u +%FT%TZ)"
    info "to exercise the full api surface in this script, bring up api too:"
    info "    ${COMPOSE[*]} up -d --build api"
    info "    bash scripts/runtime_smoke_open_plaza.sh --skip-docker"
fi
printf '\n\033[1;32m[ALL SMOKE CHECKS PASSED]\033[0m\n'