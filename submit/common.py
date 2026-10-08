"""Shared helpers for the aqora / Nexus submission scripts.

Credentials
    AQORA_TOKEN            -> aqora.Client().with_token(token)
    AQORA_CONFIG_HOME      -> <dir>/credentials.json (aqora login output)
    default                -> ~/.local/share/aqora/credentials.json (Linux)
    Note: aqora 0.35.1 `Client().authenticate()` succeeds and reports
    `authenticated == True` even with no credentials file (checked offline
    2026-10-07), so the file's existence is tested here before any job.
Team
    AQORA_TEAM_ORG         -> as_entity of every QPU (required unless
                              allow_personal=True is passed to make_qpu).
Circuits
    results/compiled/<pipeline>/<file>.qasm (hqslib1, measure-all), loaded
    with pytket and checked against compile.NATIVE.
Ledger
    results/emulator_jobs.csv, columns LEDGER_COLUMNS; append_ledger before
    submission, update_ledger after.
Results
    results/emulator/<platform>/<pipeline>/<file>.json (counts + raw dump).
"""

import csv
import datetime as _dt
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "pipelines", ROOT / "noise"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import compile as cmp  # noqa: E402  (pipelines/compile.py)
import run_proxy  # noqa: E402  (noise/run_proxy.py)
from pytket import OpType  # noqa: E402
from pytket.qasm import circuit_from_qasm_str  # noqa: E402

COMPILED = ROOT / "results" / "compiled"
RESULTS = ROOT / "results"
EMU_DIR = RESULTS / "emulator"
LEDGER = RESULTS / "emulator_jobs.csv"
BENCH = {"A": ROOT / "bench" / "family_A", "B1": ROOT / "bench" / "family_B1",
         "B2": ROOT / "bench" / "family_B2"}

PLATFORMS = ("nexus:H2-2SC", "nexus:H2-Emulator", "nexus:H2-2E")
PIPELINES = tuple(cmp.PIPELINES)
FAMILIES = ("A", "B1", "B2")

LEDGER_COLUMNS = ["timestamp", "platform", "family", "file", "pipeline", "shots",
                  "options", "job_id", "status", "hqc_or_seconds", "result_path"]

# columns of results/family_*_proxy_h22e.csv (noise/run_proxy.py) + job_id, shots
PROXY_COLUMNS = ["file", "model", "n", "r", "disorder", "instance", "pipeline",
                 "n_qubits", "n_2q", "n_1q", "n_rz", "depth_2q", "n_layers",
                 "ideal_vs_ref_maxdiff", "F_H", "TVD", "support_size", "t_sim"]
EMULATOR_COLUMNS = PROXY_COLUMNS + ["job_id", "shots"]

_A_NAME = run_proxy._NAME
_B2_NAME = re.compile(r"^haar_n(?P<n>\d+)_eps(?P<eps>[0-9.e+-]+)_s(?P<s>\d+)\.qasm$")


# ---------------------------------------------------------------- credentials

def credentials_path() -> Path:
    home = os.environ.get("AQORA_CONFIG_HOME")
    if home:
        return Path(home) / "credentials.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "aqora" / "credentials.json"
    return Path.home() / ".local" / "share" / "aqora" / "credentials.json"


def credential_source() -> str:
    """'token', 'file' or '' (none found).  No network."""
    if os.environ.get("AQORA_TOKEN"):
        return "token"
    if credentials_path().is_file():
        return "file"
    return ""


def get_client():
    """aqora.Client authenticated from AQORA_TOKEN or the credentials file.
    Raises RuntimeError when neither exists (the native client would otherwise
    silently proceed unauthenticated)."""
    import aqora
    tok = os.environ.get("AQORA_TOKEN")
    if tok:
        return aqora.Client().with_token(tok.strip())
    if credentials_path().is_file():
        return aqora.Client()
    raise RuntimeError("no aqora credentials: set AQORA_TOKEN, or run `aqora login` and point "
                       "AQORA_CONFIG_HOME at the directory holding credentials.json "
                       "(looked at %s)" % credentials_path())


def team_org(required: bool = True) -> str | None:
    org = os.environ.get("AQORA_TEAM_ORG", "").strip() or None
    if required and org is None:
        raise RuntimeError("AQORA_TEAM_ORG is not set; jobs must be submitted as the team "
                           "(as_entity), see docs/platform_notes.md 1.2")
    return org


def make_qpu(platform: str, allow_personal: bool = False):
    import aqora
    client = get_client()
    org = team_org(required=not allow_personal)
    return aqora.QPU(client, platform=platform, as_entity=org)


# ------------------------------------------------------------------ circuits

def list_family(family: str, max_n: int | None = None) -> list[dict]:
    """[{file, model, n, r, disorder, instance}] for a family, sorted by file.
    A: results/compiled/P0 names matching run_proxy._NAME (bench convention).
    B1: bench/family_B1/manifest.csv.  B2: bench/family_B2/haar_*.qasm."""
    out = []
    if family == "A":
        for f in sorted(os.listdir(COMPILED / "P0")):
            m = _A_NAME.match(f)
            if m:
                out.append(dict(file=f, model=m.group("model"), n=int(m.group("n")),
                                r=int(m.group("r")), disorder=m.group("dis"),
                                instance=int(m.group("s"))))
    elif family == "B1":
        with open(BENCH["B1"] / "manifest.csv") as fh:
            for row in csv.DictReader(fh):
                out.append(dict(file=row["file"], model=row["file"][:-5], n=int(row["n"]),
                                r="", disorder="", instance=""))
        out.sort(key=lambda d: d["file"])
    elif family == "B2":
        for f in sorted(os.listdir(BENCH["B2"])):
            m = _B2_NAME.match(f)
            if m:
                out.append(dict(file=f, model="haar", n=int(m.group("n")), r=m.group("eps"),
                                disorder="", instance=int(m.group("s"))))
    else:
        raise ValueError("unknown family %r" % family)
    if max_n is not None:
        out = [d for d in out if d["n"] <= max_n]
    return out


def compiled_path(pipeline: str, file: str) -> Path:
    return COMPILED / pipeline / file


def native_violations(circ) -> set:
    types = {cmd.op.type for cmd in circ.get_commands()}
    return {t.name for t in types - cmp.NATIVE - {OpType.Barrier}}


def load_compiled(pipeline: str, file: str, check_native: bool = True):
    """pytket Circuit from results/compiled/<pipeline>/<file>.qasm; ValueError
    if a non-native op is present."""
    p = compiled_path(pipeline, file)
    if not p.is_file():
        raise FileNotFoundError(str(p))
    circ = circuit_from_qasm_str(p.read_text())
    if check_native:
        bad = native_violations(circ)
        if bad:
            raise ValueError("%s: non-native ops %s" % (p, sorted(bad)))
        if circ.n_gates_of_type(OpType.Measure) != circ.n_qubits:
            raise ValueError("%s: expected one Measure per qubit, got %d of %d"
                             % (p, circ.n_gates_of_type(OpType.Measure), circ.n_qubits))
    return circ


def hqc_estimate(circ, shots: int) -> float:
    return cmp.hqc(circ, shots=shots)


def exact_probs(pipeline: str, file: str) -> np.ndarray:
    """Ideal Z-basis distribution of the compiled measured circuit, c[0] MSB."""
    return cmp.probs_from_measured_qasm(compiled_path(pipeline, file).read_text())


def reference_probs(family: str, file: str) -> np.ndarray:
    """Reference distribution as in noise/run_proxy.py: family A from the bench
    .npy of the circuit as written; B1 / B2 from the P0ref compilation."""
    if family == "A":
        return np.load(BENCH["A"] / (file[:-5] + ".npy"))
    return exact_probs("P0ref", file)


def circuit_stats(pipeline: str, file: str) -> dict:
    """n_2q, n_1q, n_rz, depth_2q, n_layers via run_proxy.circuit_stats."""
    gates, nq, _ = run_proxy.parse_hqslib1(compiled_path(pipeline, file).read_text())
    st = run_proxy.circuit_stats(gates)
    st["n_qubits"] = nq
    return st


# --------------------------------------------------------------- statistics

def counts_to_probs(counts: dict, n: int) -> np.ndarray:
    """Counts from aqora (keys 'b0b1...' in sorted c_bits order, so b0 = c[0];
    spaces separate registers and are dropped) -> probability vector with
    c[0] most significant, the .npy convention."""
    p = np.zeros(2 ** n)
    total = 0
    for key, c in counts.items():
        bits = key.replace(" ", "")
        if len(bits) != n:
            raise ValueError("key %r has %d bits, expected %d" % (key, len(bits), n))
        p[int(bits, 2)] += c
        total += c
    if total == 0:
        raise ValueError("empty counts")
    return p / total


def hellinger_fidelity(p, q) -> float:
    p, q = np.asarray(p, float), np.asarray(q, float)
    return float(np.sum(np.sqrt(p * q)) ** 2)


def total_variation(p, q) -> float:
    p, q = np.asarray(p, float), np.asarray(q, float)
    return float(0.5 * np.sum(np.abs(p - q)))


# ------------------------------------------------------------------- ledger

def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def read_ledger(path=LEDGER) -> list[dict]:
    path = Path(path)
    if not path.is_file():
        return []
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def _write_ledger(rows: list[dict], path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LEDGER_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in LEDGER_COLUMNS})
    os.replace(tmp, path)


def append_ledger(row: dict, path=LEDGER) -> dict:
    """Append one row (missing columns filled with ''; timestamp filled if
    absent).  Returns the row as written, which serves as the key for
    update_ledger."""
    row = dict(row)
    row.setdefault("timestamp", now_iso())
    if isinstance(row.get("options"), (dict, list)):
        row["options"] = json.dumps(row["options"], sort_keys=True)
    full = {k: ("" if row.get(k) is None else str(row.get(k, ""))) for k in LEDGER_COLUMNS}
    path = Path(path)
    new = not path.is_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LEDGER_COLUMNS)
        if new:
            w.writeheader()
        w.writerow(full)
    return full


def update_ledger(key: dict, path=LEDGER, **fields) -> int:
    """Rewrite rows matching every (column, value) in `key` with `fields`.
    Returns the number of rows updated."""
    rows = read_ledger(path)
    n = 0
    for r in rows:
        if all(str(r.get(k, "")) == str(v) for k, v in key.items()):
            for k, v in fields.items():
                if isinstance(v, (dict, list)):
                    v = json.dumps(v, sort_keys=True)
                r[k] = "" if v is None else str(v)
            n += 1
    if n:
        _write_ledger(rows, path)
    return n


# ------------------------------------------------------------------ results

def platform_dir(platform: str) -> str:
    """Directory and CSV stem for a platform. A repeat run sets EMU_RUN_TAG
    (e.g. r2) so its counts and rows go to <platform>_<tag> and do not
    overwrite the first run."""
    d = platform.replace(":", "_").replace("/", "_")
    tag = os.environ.get("EMU_RUN_TAG", "").strip()
    return d + "_" + tag if tag else d


def result_path(platform: str, pipeline: str, file: str) -> Path:
    return EMU_DIR / platform_dir(platform) / pipeline / (file[:-5] + ".json")


def save_result(platform: str, pipeline: str, file: str, payload: dict) -> Path:
    p = result_path(platform, pipeline, file)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True, default=str)
    return p


def _jsonable(x):
    try:
        json.dumps(x)
        return x
    except TypeError:
        return repr(x)


def dump_object(obj) -> dict:
    """Every public attribute and property of an aqora object, repr'd when not
    JSON-serialisable, so no provider field is lost."""
    out = {}
    for name in dir(obj):
        if name.startswith("_"):
            continue
        try:
            v = getattr(obj, name)
        except Exception as e:  # noqa: BLE001
            out[name] = "<error %s>" % e
            continue
        if callable(v):
            continue
        out[name] = _jsonable(v)
    return out


def job_raw(job) -> dict:
    """Refreshed GraphQL payload of a job (id, platform, status, error,
    duration, resultCount, createdAt) plus its public attributes."""
    try:
        payload = dict(job.refresh())
    except Exception as e:  # noqa: BLE001
        payload = {"refresh_error": repr(e)}
    return {"payload": payload, "attributes": dump_object(job)}


def result_raw(res) -> dict:
    d = dump_object(res)
    d["raw"] = getattr(res, "raw", None)
    return d


def cost_fields(payload: dict) -> dict:
    """Whatever cost-like fields the job payload carries (aqora 0.35.1 exposes
    only `duration`; any key containing cost/hqc/credit is also picked up)."""
    out = {}
    for k, v in payload.items():
        kl = k.lower()
        if kl == "duration" or "cost" in kl or "hqc" in kl or "credit" in kl:
            out[k] = v
    return out


def wait_counts(job, timeout: float, poll: float = 5.0):
    """job.counts(timeout=..., wait=...) with wall time."""
    t0 = time.perf_counter()
    counts = job.counts(timeout=timeout, wait=poll)
    return counts, time.perf_counter() - t0
