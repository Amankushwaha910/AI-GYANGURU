"""
End-to-end smoke test against the running backend (http://localhost:8000).
Run from: backend/
  python scripts/smoke_test.py
"""
import asyncio
import json
import sys
import httpx

BASE = "http://localhost:8000/api/v1"
EMAIL = "smoketest@gyanguru.dev"
PASSWORD = "Smoke@Test1"

GREEN = "\033[92m"
RED   = "\033[91m"
RESET = "\033[0m"
BOLD  = "\033[1m"

passed = 0
failed = 0

def ok(label: str, detail: str = ""):
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET} {label}" + (f"  →  {detail}" if detail else ""))

def fail(label: str, detail: str = ""):
    global failed
    failed += 1
    print(f"  {RED}✗{RESET} {label}" + (f"  →  {detail}" if detail else ""))

async def main():
    async with httpx.AsyncClient(timeout=30) as c:

        # ── Health ────────────────────────────────────────────────────────
        print(f"\n{BOLD}Health{RESET}")
        r = await c.get("http://localhost:8000/health")
        if r.status_code == 200: ok("GET /health", r.json().get("status"))
        else: fail("GET /health", str(r.status_code))

        # ── Register (ignore 400/409 conflict = already registered) ──────────
        print(f"\n{BOLD}Auth{RESET}")
        r = await c.post(f"{BASE}/auth/register", json={
            "email": EMAIL, "password": PASSWORD, "full_name": "Smoke Tester"
        })
        if r.status_code == 201:
            ok("POST /auth/register", "new user created")
        elif r.status_code in (400, 409, 422) and "already exists" in r.text:
            ok("POST /auth/register", "user already exists (expected on re-run)")
        else:
            fail("POST /auth/register", r.text[:120])

        # ── Login ────────────────────────────────────────────────────────
        r = await c.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": PASSWORD})
        if r.status_code == 200:
            token = r.json()["data"]["access_token"]
            ok("POST /auth/login", "token received")
        else:
            fail("POST /auth/login", r.text[:120])
            print(f"\n{RED}Cannot continue without a token.{RESET}")
            return

        headers = {"Authorization": f"Bearer {token}"}

        # ── Me ────────────────────────────────────────────────────────────
        r = await c.get(f"{BASE}/auth/me", headers=headers)
        if r.status_code == 200:
            ok("GET /auth/me", r.json()["data"]["email"])
        else:
            fail("GET /auth/me", r.text[:120])

        # ── Dashboard ─────────────────────────────────────────────────────
        print(f"\n{BOLD}Dashboard{RESET}")
        r = await c.get(f"{BASE}/dashboard", headers=headers)
        if r.status_code == 200:
            s = r.json()["data"]["summary"]
            ok("GET /dashboard", f"topics={s['total_topics_studied']} quizzes={s['total_quizzes_taken']}")
        else:
            fail("GET /dashboard", r.text[:120])

        # ── Analytics ─────────────────────────────────────────────────────
        print(f"\n{BOLD}Analytics{RESET}")
        r = await c.get(f"{BASE}/analytics/dashboard", headers=headers)
        if r.status_code == 200:
            ok("GET /analytics/dashboard")
        else:
            fail("GET /analytics/dashboard", r.text[:120])

        # ── Summary ───────────────────────────────────────────────────────
        print(f"\n{BOLD}Summary{RESET}")
        r = await c.post(f"{BASE}/summaries", headers=headers, json={
            "topic": "Newton's Laws of Motion",
            "sections": ["definition", "key_concepts", "revision_notes"]
        })
        if r.status_code == 201:
            d = r.json()["data"]
            ok("POST /summaries", f"topic={d['topic']} words={d.get('word_count')}")
            summary_id = d["id"]
        else:
            fail("POST /summaries", r.text[:200])
            summary_id = None

        if summary_id:
            r = await c.get(f"{BASE}/summaries/{summary_id}", headers=headers)
            if r.status_code == 200: ok(f"GET /summaries/{{id}}")
            else: fail(f"GET /summaries/{{id}}", r.text[:120])

        # ── Explanation ───────────────────────────────────────────────────
        print(f"\n{BOLD}Explanation{RESET}")
        r = await c.post(f"{BASE}/explanations", headers=headers, json={
            "topic": "Photosynthesis"
        })
        if r.status_code == 201:
            d = r.json()["data"]
            ok("POST /explanations", f"topic={d['topic']}")
        else:
            fail("POST /explanations", r.text[:200])

        # ── Quiz ──────────────────────────────────────────────────────────
        print(f"\n{BOLD}Quiz{RESET}")
        r = await c.post(f"{BASE}/quizzes", headers=headers, json={
            "topic": "French Revolution",
            "question_count": 5,
            "difficulty": "easy"
        })
        if r.status_code == 201:
            d = r.json()["data"]
            quiz_id = d["id"]
            questions = d["questions"]
            ok("POST /quizzes", f"id={quiz_id} questions={len(questions)}")
        else:
            fail("POST /quizzes", r.text[:200])
            quiz_id = None
            questions = []

        if quiz_id and questions:
            r = await c.get(f"{BASE}/quizzes/{quiz_id}", headers=headers)
            if r.status_code == 200: ok("GET /quizzes/{id}")
            else: fail("GET /quizzes/{id}", r.text[:120])

            # Submit quiz
            answers = [{"question_id": q["id"], "selected_option": "A"} for q in questions]
            r = await c.post(f"{BASE}/quizzes/{quiz_id}/submit", headers=headers, json={
                "answers": answers, "time_taken_seconds": 30
            })
            if r.status_code == 200:
                d = r.json()["data"]
                attempt_id = d["id"]
                ok("POST /quizzes/{id}/submit", f"score={d['score']}/{d['total_questions']} ({d['percentage']:.0f}%)")
            else:
                fail("POST /quizzes/{id}/submit", r.text[:200])
                attempt_id = None

            if attempt_id:
                r = await c.get(f"{BASE}/quizzes/{quiz_id}/attempts/{attempt_id}", headers=headers)
                if r.status_code == 200: ok("GET /quizzes/{id}/attempts/{id}")
                else: fail("GET /quizzes/{id}/attempts/{id}", r.text[:120])

        # ── Files list ────────────────────────────────────────────────────
        print(f"\n{BOLD}Files{RESET}")
        r = await c.get(f"{BASE}/files", headers=headers)
        if r.status_code == 200:
            ok("GET /files", f"count={r.json()['total']}")
        else:
            fail("GET /files", r.text[:120])

        # ── History ───────────────────────────────────────────────────────
        print(f"\n{BOLD}History{RESET}")
        r = await c.get(f"{BASE}/history", headers=headers)
        if r.status_code == 200:
            ok("GET /history", f"total={r.json()['total']}")
        else:
            fail("GET /history", r.text[:120])

        # ── Logout ────────────────────────────────────────────────────────
        print(f"\n{BOLD}Logout{RESET}")
        r = await c.post(f"{BASE}/auth/logout", headers=headers, json={})
        if r.status_code == 200: ok("POST /auth/logout")
        else: fail("POST /auth/logout", r.text[:120])

    # ── Summary ───────────────────────────────────────────────────────────
    total = passed + failed
    color = GREEN if failed == 0 else RED
    print(f"\n{'─'*50}")
    print(f"{color}{BOLD}{passed}/{total} checks passed{RESET}")
    if failed: print(f"{RED}{failed} failed{RESET}")
    print()
    sys.exit(0 if failed == 0 else 1)

asyncio.run(main())
