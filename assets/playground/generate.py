# Writes the generated scenario of the playground, the same every run (fixed seed):
#   playground/incidents/  30 incident reports, a few caused by the database
# It lives outside the playground so the agent cannot read the answers from it.
#
#   python3 assets/playground/generate.py            # write the reports
#   python3 assets/playground/generate.py --answers  # print the answers, for the instructor

import random
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

PLAYGROUND = Path(__file__).resolve().parents[2] / "playground"
REPORTS = 30
# Log lines per report: about 900 tokens a report, so 10 fit one subagent well below compaction (16k of
# 32k) and all 30 do not.
LOG_LENGTH = 25

# --- incidents ---------------------------------------------------------------------------------------

SERVICES = ["checkout", "search", "accounts", "payments", "catalog", "notifications", "reports", "login"]
# (caused by the database, root cause, what the logs show). A database cause starts with "The database", so
# the question has one answer; the decoys say the database was healthy.
CAUSES = [
    (True, "The database ran out of connections: a batch job filled the pool of the primary Postgres database and never closed them.",
     "pool exhausted: 100/100 connections in use, waiting for a free connection"),
    (True, "The database locked the orders table for a long-running migration, so every write to it waited until the migration finished.",
     "lock wait timeout exceeded on table orders"),
    (True, "The database's read replica fell 9 minutes behind after a disk slowdown, so reads returned old data.",
     "replica lag 540s, read from replica returned stale row"),
    (True, "The database ran out of disk space on its volume because old write-ahead log files were never archived.",
     "could not extend file: No space left on device (database volume)"),
    (True, "The database CPU was saturated: a missing index on sessions.user_id made a new query scan the whole table.",
     "slow query 14.2s: SELECT * FROM sessions WHERE user_id = $1"),
    (False, "An expired TLS certificate on the internal load balancer made clients reject every connection.",
     "x509: certificate has expired or is not yet valid"),
    (False, "A deploy shipped a config file with the cache host misspelled, so every request missed the cache.",
     "cache connect failed: unknown host redis-mian.internal"),
    (False, "A memory leak in the image resizer filled the container's memory until the kernel killed it.",
     "OOMKilled: container exceeded its 2Gi memory limit"),
    (False, "The upstream payment provider rate-limited our API key after a retry loop sent each request ten times.",
     "429 Too Many Requests from payment provider"),
    (False, "A DNS change pointed the API name at the old data center, which no longer had any servers.",
     "dial tcp: lookup api.internal: no such host"),
    # Red herrings: the logs show database timeouts, but the database was fine.
    (False, "A network switch in rack 12 dropped packets. The database timeouts in the logs were a symptom: the database itself was healthy.",
     "db query timeout after 5000ms (network: 38% packet loss to 10.0.12.0/24)"),
    (False, "A bad deploy of the accounts service retried every failed request without a pause, which overloaded its own workers. Database latency looked high only because requests queued in the service.",
     "db call took 4100ms (queued 4050ms in worker pool)"),
]
LOG_LINES = [
    "GET /api/{svc}/items 200 {ms}ms", "POST /api/{svc}/orders 201 {ms}ms", "health check ok ({ms}ms)",
    "GET /api/{svc}/search?q=lamp 200 {ms}ms", "cache hit ratio 0.{n}", "worker {n} picked up job",
    "GET /api/{svc}/users/me 200 {ms}ms", "gc pause {n}ms", "POST /api/{svc}/events 202 {ms}ms",
]


def incidents(rng):
    folder = PLAYGROUND / "incidents"
    shutil.rmtree(folder, ignore_errors=True)
    folder.mkdir()
    # Every cause twice, red herrings included, plus a few more: 30 reports in a fixed, shuffled order.
    causes = CAUSES * 2 + rng.sample(CAUSES, REPORTS - 2 * len(CAUSES))
    rng.shuffle(causes)
    start = datetime(2026, 3, 2, 9, 0)
    answers = []
    for i, (database, cause, symptom) in enumerate(causes, 1):
        when = start + timedelta(days=i * 7 + rng.randrange(5), hours=rng.randrange(14), minutes=rng.randrange(60))
        svc = rng.choice(SERVICES)
        minutes = rng.randrange(12, 95)
        number = f"INC-{2600 + i}"
        log = []
        t = when - timedelta(minutes=10)
        for n in range(LOG_LENGTH):
            t += timedelta(seconds=rng.randrange(5, 25))
            if n > 8 and n % 4 == 0:
                line = f"ERROR {symptom}"
            else:
                line = "INFO " + rng.choice(LOG_LINES).format(svc=svc, ms=rng.randrange(8, 400), n=rng.randrange(10, 99))
            log.append(f"{t:%H:%M:%S} {svc}-{rng.randrange(1, 6)} {line}")
        (folder / f"{number}.md").write_text(f"""# {number}: {svc} degraded

- Date: {when:%Y-%m-%d}, {when:%H:%M} UTC
- Service: {svc}
- Severity: {rng.choice(["SEV1", "SEV2", "SEV2", "SEV3"])}
- Duration: {minutes} minutes

## Timeline

- {when:%H:%M} Alert: error rate of {svc} above 5%.
- {(when + timedelta(minutes=4)):%H:%M} On-call engineer acknowledged and started looking at the logs.
- {(when + timedelta(minutes=minutes // 2)):%H:%M} Cause found, fix started.
- {(when + timedelta(minutes=minutes)):%H:%M} Error rate back to normal. Incident closed.

## Logs

```
{chr(10).join(log)}
```

## Root cause

{cause}

## Follow-ups

- Add an alert for this failure mode.
- Write a runbook entry for the on-call engineer.
""")
        if database:
            answers.append(f"{number} ({when:%Y-%m-%d}): {cause}")
    (folder / "README.md").write_text(f"""# Incidents

{REPORTS} incident reports, one per file: `INC-2601.md` to `INC-{2600 + REPORTS}.md`. Each has a date, the service, a timeline, the logs and, at the end, the root cause. The logs of one report fill several screens.
""")
    return answers


def main():
    answers = incidents(random.Random(2026))
    if "--answers" in sys.argv:
        print(f"incidents caused by the database ({len(answers)}):")
        print("\n".join(f"  {a}" for a in answers))
    else:
        print(f"wrote {PLAYGROUND / 'incidents'}")


if __name__ == "__main__":
    main()
