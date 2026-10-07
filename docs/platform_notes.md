# Platform notes: aqora, Aqora Grand Challenge submission, Quantinuum H2 emulators, Selene

Compiled 2026-10-06 (UTC) from the installed `aqora` 0.35.1 package, the public aqora docs, the anonymous aqora GraphQL endpoint, and docs.quantinuum.com. Read-only research: nothing was logged in to, no job was submitted, no account was created. Every claim carries its source (URL or file path) and a verbatim quote. `[F]` = fact verifiable from the quoted source or from a command run here. `[O]` = my reading of the facts.

Source files of the installed package are under `/usr/local/lib/python3.13/dist-packages/aqora/` (abbreviated `aqora/` below).

---

## 1. aqora Python API for Quantinuum platforms

### 1.1 Entry points that exist in the installed source

[F] `aqora/__init__.py` exports: `from .qpu import QPU, QPUJob`, `from ._provider.jobs import ProviderJob`, `from ._provider.results import ProviderResult`, `from .auth import viewer_login`, `from .store import Store, StoreCredentials`, `from .kv import KV`, plus `Client` and the `QIO_*` constants from the native module `aqora._aqora` (`from aqora._aqora import *`).

[F] There is no `aqora.auth` module exposing a token function for scripts. `aqora/auth.py` defines only `viewer_login` (marimo consent flow) and `_local_login`. Authentication for scripts is done by `Client` (native, see 1.4).

### 1.2 `aqora.QPU(platform=...)`

[F] `aqora/qpu.py` lines 46-55, constructor signature:

```python
def __init__(self, client: Client | None = None, *, url: str | None = None,
             allow_insecure_host: bool | None = None, platform: str | None = None,
             as_entity: str | None = None, compress: bool = True) -> None:
```

[F] Class docstring (`aqora/qpu.py` lines 27-44): "`platform` selects the provider platform by name or id (the schema's `ProviderPlatformNameOrID`). When it is omitted the server chooses a default platform that this client cannot identify ... `as_entity` is the username or id of an organization you belong to; jobs are attributed to it, which is how provider quota is tracked per team. When it is omitted jobs are attributed to you personally."

[F] Public docs, https://docs.aqora.io/llms-full.txt (section "Submitting as a team"): "Team members must submit as the team. When `as_entity` is omitted the job is attributed to you personally, and you must be a member of the provider platform yourself."

[O] For the challenge, every `QPU(...)` call should carry `as_entity="<team organization username>"`; the team's aqora organization username is not known from here.

### 1.3 `QPU.run(circuit, shots=...)`

[F] `aqora/qpu.py` lines 90-97:

```python
def run(self, programs: Any, *, shots: int, wasm: Any = None,
        options: Mapping[str, Any] | None = None) -> "QPUJob":
```

[F] Docstring (lines 98-119): "`shots` is required: every program in the job runs that many times. `programs` is a single program, or a list or tuple of them. Accepted programs are qiskit `QuantumCircuit`s, pytket `Circuit`s, `@guppy`-decorated functions, hugr `Package`s, raw HUGR envelope or QIR bitcode bytes, and QASM source. ... `options` are backend options for the job. Nexus H-series devices and emulators accept `noisy_simulation`, `simulator`, `error_params`, `compiler_options`, `no_opt`, `allow_2q_gate_rebase`, `target_2qb_gate`, `leakage_detection` and `simplify_initial`; other platforms accept none, and the server rejects the job before it runs."

[F] `shots` validation (`aqora/_provider/jobs.py` `normalize_shots`, lines 69-91): rejects `None`, bools, non-integers, and values `< 1`.

[F] Wire format: `run` detects each program's format and encodes to the first format in the platform's `meta.inputFormats` list (`aqora/qpu.py` lines 120-122, `_load_input_formats` lines 139-154). Format constants in `aqora._aqora`, read at runtime:

| constant | value |
|---|---|
| `QIO_PROGRAM_QASM_V1 / V2 / V3` | 1 / 2 / 3 |
| `QIO_PROGRAM_QIR_V1` | 4 |
| `QIO_PROGRAM_CIRQ_CIRCUIT_JSON_V1` | 5 |
| `QIO_PROGRAM_PERCEVAL_CIRCUIT_JSON_V1` | 6 |
| `QIO_PROGRAM_PULSER_SEQUENCE_JSON_V1` | 7 |
| `QIO_PROGRAM_TKET_CIRCUIT_JSON_V1` | 1000 |
| `QIO_PROGRAM_HUGR_V1` | 1001 |
| `QIO_RESULT_CIRQ_RESULT_JSON_V1` | 1 |
| `QIO_RESULT_QISKIT_RESULT_JSON_V1` | 2 |
| `QIO_RESULT_CUDAQ_SAMPLE_RESULT_JSON_V1` | 3 |
| `QIO_RESULT_PYTKET_BACKEND_RESULT_JSON_V1` | 1000 |
| `QIO_RESULT_QIR_LABELED_RESULT_V1` | 1001 |
| `QIO_RESULT_QSYS_RESULT_JSON_V1` | 1002 |

### 1.4 Authentication: how it works, and how to run from this shell

[F] https://docs.aqora.io/llms-full.txt, section "Authentication":
- "`aqora login` ... This opens your browser to authorize the CLI with your aqora account. If no browser can be opened, the CLI prints the authorization URL along with a QR code you can scan from another device."
- "On a machine where completing a browser flow isn't possible at all — over SSH, for example — log in with your username and password directly in the terminal: `aqora login --interactive`"
- "Credentials are saved in your platform's data directory and refreshed automatically when they expire: Linux `~/.local/share/aqora/credentials.json` ... The location can be overridden with `--config-home` or the `AQORA_CONFIG_HOME` environment variable."
- "The aqora Python library reads the same file, so after `aqora login` you can use `from aqora import QPU` without any further setup."
- "To use your session outside the CLI — with `curl` or another API client — print a valid access token (refreshing it first if needed): `aqora auth token`"

[F] `aqora login --help` run here: `-i, --interactive  Force login without a browser`; global option `--config-home <CONFIG_HOME>  [env: AQORA_CONFIG_HOME=]`. `aqora auth --help`: subcommand `token  Print a valid aqora access token on stdout, refreshing if needed`.

[F] `credentials.json` schema, from strings in `aqora/_aqora.abi3.so`: `struct CredentialsFile with 1 element`, `struct Credentials with 5 elements`, field names `client_id client_secret access_token refresh_token expires_at`. The file is written by the login flow (OAuth2 mutations `oauth2Token` / `oauth2Refresh` appear in the same binary). There is no documented way to hand-write it from a username/password.

[F] Token-in-code alternative: `aqora/_aqora.pyi` declares `Client.with_token(self, token: str) -> Client`, docstring (read at runtime): "A client authenticating every GraphQL request with `token`." The `Client` also has `authenticated: bool` and `async authenticate()`. `QPU(client=...)` accepts such a client (`aqora/qpu.py` line 48). So a token obtained elsewhere (e.g. `aqora auth token` on the user's laptop) can be used as `QPU(Client().with_token(TOKEN), platform=...)`.

[F] Env vars recognised by the native client (strings in `_aqora.abi3.so`): `AQORA_URL`, `AQORA_ALLOW_INSECURE_HOST`, `AQORA_CONFIG_HOME`, `DO_NOT_TRACK`. No `AQORA_TOKEN`-style variable appears in the binary or the docs. [O] Token injection must therefore go through `Client.with_token` in code or through the credentials file.

[F] Inside an aqora workspace no login is needed. `aqora/_aqora.abi3.so` embeds this guidance: "The kernel is already authenticated as the workspace owner, so never run `aqora login` or ask for credentials." Docs: "Inside a marimo notebook in an aqora.io workspace there is nothing to do: the workspace is already authenticated on your behalf."

[F] State of this shell on 2026-10-06: `~/.local/share/aqora/` and `~/.config/aqora/` do not exist; no credentials present. Nothing was created.

**Running outside the Aqora notebook from this shell, what the user must provide** [O, derived from the facts above]:
- Option A (credentials file): on his laptop run `aqora login` (or `aqora login --interactive`), then copy `~/.local/share/aqora/credentials.json` (Linux) / `~/Library/Application Support/aqora/credentials.json` (macOS) into the same path here, or into any directory and set `AQORA_CONFIG_HOME=<that dir>`. The file holds a refresh token, so it keeps working after the access token expires.
- Option B (short-lived token): on his laptop run `aqora auth token`, paste the printed token; use `QPU(aqora.Client().with_token(token), platform=..., as_entity=...)`. Expires when the access token expires (lifetime not published).
- Option C: run `aqora login --interactive` in this shell with his username and password typed in. Not used here (no credentials, instruction was not to log in).

### 1.5 Platform names

[F] Anonymous query to `https://aqora.io/graphql` (`providerPlatforms(first: 100)`) on 2026-10-06, all `provider: NEXUS`, all `private: true`:

| name | maxQubits | inputFormats |
|---|---|---|
| `aer_simulator_statevector` | 26 | TKET_CIRCUIT_JSON_V1 |
| `Selene` | 26 | HUGR_V1, QIR_V1 |
| `H2-Emulator` | null | TKET_CIRCUIT_JSON_V1 |
| `H2-1E` | null | TKET_CIRCUIT_JSON_V1, QIR_V1 |
| `H2-2E` | null | TKET_CIRCUIT_JSON_V1, QIR_V1 |
| `H2-1SC` | null | TKET_CIRCUIT_JSON_V1, QIR_V1 |
| `H2-2SC` | null | TKET_CIRCUIT_JSON_V1, QIR_V1 |

`maxShots` and `maxCircuits` were `null` for every platform. `hasNextPage: false`, so this is the whole list. Saved as `/tmp/.../scratchpad/dl/platforms.json` (session-only).

[F] Name form: `aqora/_provider/jobs.py` `platform_matches` docstring: "Accepts the platform's global id, its bare name, or the server's `provider:name` form ... the provider segment is the lowercase enum value, e.g. `nexus:Selene`." So `"nexus:H2-2E"`, `"nexus:H2-Emulator"`, `"nexus:H2-2SC"`, `"nexus:Selene"` are valid, and bare `"H2-2E"` also matches.

[F] `private: true` for all: `createProviderJob` mutation description (GraphQL introspection): "On a private platform that entity itself must be a member: a viewer whose organization is the member must pass the organization as `asEntity`, which requires being one of its Owners or Admins." [O] The user (or whoever submits) must be Owner/Admin of the team organization on aqora, or a direct member of the platform.

[F] pytket circuits go to `H2-*` platforms as `TKET_CIRCUIT_JSON_V1` (first preferred format). For `Selene` the preferred formats are HUGR/QIR; docs: "`aqora[pytket-qir]` pytket circuits to QIR ... If a conversion is unavailable, the error tells you which extra to install." `pytket-qir 2.0.2` is installed here.

### 1.6 `noisy_simulation` and other options

[F] Public docs (https://docs.aqora.io/llms-full.txt, "WASM modules and emulator options"): "`options` sets emulator options such as `noisy_simulation`: `qpu = QPU(platform="nexus:H2-1E"); job = qpu.run(circ, shots=10, wasm="decoder.wasm", options={"noisy_simulation": False})`".

[F] Same docs, "Emulator options" (pytket backend): "The supported keys are `noisy_simulation`, `simulator`, `error_params`, `compiler_options`, `no_opt`, `allow_2q_gate_rebase`, `target_2qb_gate`, `leakage_detection` and `simplify_initial`. Only the options you pass are sent, so Nexus' defaults (such as noisy simulation on the emulators) apply to the rest. Any other key, or any option on another platform, is rejected before the job is submitted."

[F] Server side, `createProviderJob` argument `options: JSON` exists in the live schema (introspected 2026-10-06), description: "Nexus H-series devices and emulators accept a subset of their `QuantinuumConfig` (`noisy_simulation`, `simulator`, `error_params`, `compiler_options`, `no_opt`, `allow_2q_gate_rebase`, `target_2qb_gate`, `leakage_detection`, `simplify_initial`); other platforms accept none. A null option is the same as leaving it out. The job is rejected before anything is submitted when an option isn't accepted."

[F] Client side, `aqora/_provider/jobs.py` `submit_model` sends `options` only if non-empty, via the optional GraphQL argument (`aqora/_provider/client.py` `create_provider_job`, `if options: optional.append(("options", "JSON"))`). `aqora/pytket/backend.py` line 44: `_QUANTINUUM_OPTION_KWARGS = ("noisy_simulation", "leakage_detection", "simplify_initial")` forwarded from `process_circuits(..., noisy_simulation=False)`.

[O] The forum post saying `noisy_simulation` cannot be passed is stale relative to aqora 0.35.1 and the current schema: both the client and the server declare it. Whether the `H2-Emulator` (Nexus tier) platform accepts `noisy_simulation: False` in practice was not tested (no job submitted). The docs' own example uses `nexus:H2-1E`.

### 1.7 Jobs and results

[F] `aqora/qpu.py` `QPUJob`:
- `QPUJob.from_id(job_id, *, client=None, url=None, allow_insecure_host=None)` (lines 170-187): "Load a job by id, building its `QPU` from the job's platform." `serialization_format` is `None` for such a job.
- `result(timeout=None, wait=5.0) -> ProviderResult` (line 200): single-program job only, else `RuntimeError`.
- `result_items() -> list[ProviderResult]`.
- `counts(timeout=None, wait=5.0) -> list[dict[str, int]]` (lines 214-225): "Wait for the job and normalize each result to counts. One mapping per program, in submission order, whatever format the provider returned."
- Inherited from `ProviderJob` (`aqora/_provider/jobs.py`): `refresh()`, `status()`, `error()`, `wait(timeout=None, poll_interval=5.0)`, `results(raise_on_item_error=True)`.

[F] Status values (GraphQL enum `ProviderJobStatus`, introspected): `WAITING, RUNNING, COMPLETED, CANCELLING, CANCELLED`. Failure detection (`is_provider_failure`): "The server nulls `status` and puts the provider's message in `error` when the provider reports an error state."

[F] `ProviderJob` GraphQL fields (introspected): `id, viewerCan, providerModel, entity, provider, platform, status, error, duration, resultCount, createdAt, resultUploadAttempts, workspaceVersionId, results`. [O] `duration` is the only cost-like field; no HQC field is exposed on the job object, so HQC cost must be read from the syntax checker result or from Nexus.

[F] Result format (`aqora/_provider/results.py`): `ProviderResult(index, serialization_format, raw, error=None)`. `counts()` dispatches on format: pytket `BackendResult` JSON (1000) -> `to_backend_result().get_counts()` with register groups joined by a space; QSYS (1002) -> `to_qsys_result().collated_counts()`; labeled QIR (1001) -> joint counts from the `START/OUTPUT/END` tab-separated shot protocol; qiskit (2), cirq (1), CUDA-Q (3). Docstring: "Keys are bitstrings; a result carrying several named registers joins their values with a space in label order ... Counts are always joint over the registers of a shot, never a product of per-register marginals." [O] For a pytket circuit on `H2-2E` the result will be format 1000 and `result.to_backend_result()` gives the full pytket `BackendResult` (shots table) besides counts.

[F] `aqora job model <id>` CLI subcommand: "Download the model payload a provider job ran" (`aqora job --help`).

### 1.8 Framework backends

[F] `aqora.pytket.QPU` is a pytket `Backend` (`get_compiled_circuit`, `process_circuit(s)`, `get_result`); `aqora.qiskit.QPU` a `BackendV2`; `aqora.guppy.QPU` for guppy/HUGR. Docs: "All three take the same constructor arguments as the universal `QPU`, including `platform="provider:name"` and `as_entity="my-team"`." `default_compilation_pass()` "runs a client-side optimisation pipeline; the server owns device-level compilation".

---

## 2. Submission mechanics on Aqora (Quantinuum Singapore Grand Challenge)

### 2.1 What is visible without login

[F] `curl -L https://aqora.io/challenges/quantinuum-sg-grand-challenge` (2026-10-06) returns HTTP 200 with the page text: "Not Found 404 Challenge not found Try logging in to view this page." Same for `/tracks`, `/discussions`, `/rules` (all "Challenge not found Try logging in to view this page"), `/templates` and `/leaderboard` ("Not Found 404"), `/submissions` ("No submissions found"). `https://aqora.io/competitions/quantinuum-sg-grand-challenge` and `https://aqora.io/events/quantinuum-sg-grand-challenge` likewise render the 404 shell.

[F] Anonymous GraphQL: `competitionBySlug(slug:"quantinuum-sg-grand-challenge")` -> `null`; `eventBySlug(slug:"quantinuum-sg-grand-challenge")` -> `null`.

[O] The challenge is private: the submission form, the track list, the template and the discussion thread all need the user's login. The exact slug may also differ from `quantinuum-sg-grand-challenge`; this cannot be confirmed anonymously.

### 2.2 The data model behind "Submit to Track" (from the live GraphQL schema, introspected anonymously)

[F] Challenge = `Event`, Track = `Competition`. Mutation `createEventFromCompetition` description: "Create an event (challenge) from a competition (track) It's derive all competition (track) metadata to properlly create an event (challenge)". `Event` has fields `competition`, `competitions`, `teams`, `invitations`, `rules`.

[F] Workspace versions: `createWorkspaceVersion(id, input{version: Semver, fromVersionId})` "Create a new draft version of a workspace."; `publishWorkspaceVersion(id)` "Publish a draft version. It becomes read-only and viewable through its `renderer`." `WorkspaceVersion` has `overviewNotebook` ("this version's override if set, else the auto-detected default from this version's own files"), `libNotebook`, `fromCompetition` ("The competition (track) whose template this version derives from, if any"), and `submissions` ("Submissions (visible to the viewer) that link this workspace version").

[F] Linking a published notebook version to the track submission: `setSubmissionWorkspaceVersions(competitionId: ID!, workspaceVersionIds: [ID!]!, asEntity: UsernameOrID)`, description: "Replace the set of published workspace versions linked to the viewer's (team's) submission for a simple/no-code competition. The submission (and an empty placeholder version) is created if it doesn't exist yet, so a link-only submission still surfaces in the leaderboard/approval flows."

[F] File upload route: `uploadNoCodeSubmissionVersion(competitionId: ID!, input: {files: [Upload!]!}, asEntity)`, description: "Submit files for a "no-code" competition. This feature is not available for regular competitions." The `files` element type is the GraphQL `Upload` scalar.

[F] Code-submission route (regular competitions): `createSubmissionVersion(competitionId, input: {pyprojectToml: String!, readme: String, compression}, asEntity)`; this is what `aqora upload [COMPETITION]` drives (CLI help; binary strings "Validating submission", "No [tool.aqora] section found in pyproject.toml").

[F] `CompetitionStage` fields include `noCode: Boolean!`, `requiresApproval`, `useJuryScore`, `submissionPreamble: String`, `scoringCriteria` (each `CompetitionScoringCriterion` has `title, order, description, weight`). `Competition` has `templates`, `rules`, `latestRule`, `viewerWorkspace`, `teamRequests`.

[O] Reading of the above: "publish a Marimo notebook version, then Submit to Track" corresponds to `publishWorkspaceVersion` followed by `setSubmissionWorkspaceVersions` (web UI buttons), submitted `asEntity` = the team. Whether the Grand Challenge track is flagged `noCode` (which would also enable `uploadNoCodeSubmissionVersion` for a PDF) and whether the form asks for a report attachment cannot be determined without login. The scoring criteria (`scoringCriteria` with weights) and `submissionPreamble` of the active stage are exactly what the logged-in page shows above the submit button; the user can read them with the MCP server (section 2.3) or in the browser.

### 2.3 Read-only way for the user to fetch the form details

[F] Docs (https://docs.aqora.io/llms-full.txt, "MCP server"): aqora runs an MCP server at `https://aqora.io/mcp` with "one tool, `run_graphql`, which runs queries and mutations against the full aqora GraphQL API as you". Warning quoted: "An assistant connected this way can do everything your account can, including possibly non-reversible actions."

[O] Alternatively, with a token from `aqora auth token`, this query (run with `Authorization: Bearer <token>` against `https://aqora.io/graphql`) returns the track, its active stage, scoring criteria and preamble:

```graphql
query { eventBySlug(slug: "quantinuum-sg-grand-challenge") { id title
  competitions(first: 10) { nodes { competition { id slug title
    currentStage { noCode requiresApproval submissionPreamble validUntil
      scoringCriteria { title weight description } } } } } } }
```
(Field names verified by introspection; the slug is unverified.)

---

## 3. Quantinuum docs: H2-2E noise model, HQC formula, H2-Emulator tier, Selene

### 3.1 Emulator tiers

[F] https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/introduction.html: "There are two emulator offerings available to users (full table specification below), Nexus-hosted emulators (suffixed Emulator) and hardware-tier emulators (suffixed E). Nexus-hosted emulators correspond to each generation of Quantinuum quantum computers and are costed in time. Hardware-tier emulators are provided per machine instance per generation, and are costed in Hardware Quantum Credits (HQCs). Hardware-tier emulators use a global Fair queue based on organization accumulation for a pre-defined interval. Nexus-hosted emulators require a user-specific Fair queue conditioned on maximum number of concurrent simulation jobs a user is running."

[F] Same page, "Emulator Specification" table (columns: Target | qubits statevector | qubits stabilizer | Tier | Currency | Noise Model | Chunking | Batching): `H2-1E | 32 | 56 | Hardware | HQC | ✔ | ✔ | ✗`, `H2-2E | 32 | 56 | Hardware | HQC | ✔ | ✔ | ✗`, `H2-Emulator | 26 | 26 | Nexus | Seconds | ✔ | ✗ | ✗`.

[F] https://docs.quantinuum.com/systems/trainings/h2/getting_started/emulators.html: "Nexus-hosted Emulators: Per generation instances of Quantinuum emulators are hosted in Nexus. The HX-Emulator (X is an integer specifying machine generation) targets enable state-vector and stabilizer emulation whilst including the physical noise model of the Quantinuum device." and "For smaller noiseless emulations involving less than 16 qubits, it is recommended to use the nexus-hosted emulators. For larger emulations, or emulations using a noise model, cloud emulators is recommended."

[F] https://docs.quantinuum.com/nexus/user_guide/concepts/backends.html: "'Hosted by Nexus' means that use will be via your Nexus quota and Nexus's internal job queue, whereas 'Hosted by Quantinuum' means that use will be via your Hardware Quantum Credits (HQC)".

[O] Which of H2-1 / H2-2 the `H2-Emulator` noise model represents is not stated on these pages ("per generation"). The aqora discussion thread's phrase "average error model" (recorded in the project plan) is not in the Quantinuum docs I fetched.

### 3.2 What the H2 emulator noise model contains

[F] https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/noise_model.html:
- 1q/2q gates: "The 1- and 2-qubit fault probabilities are largely modeled using asymmetric depolarizing channels; however, there is smaller probability that a spontaneous emission event happens. The probability is about an order of magnitude lower than the corresponding asymmetric depolarizing error rate. ... If a spontaneous emission event happens then 1/4 the time Pauli-X is applied, 1/4 the time Pauli-Y is applied, and 1/2 the time leakage is applied".
- Angle dependence: "The probability of asymmetric depolarizing error for the parameterized angle 2-qubit gate, RZZ(θ), depends on the angle θ." Scaling: `(przz_a (|θ|/π)^przz_power + przz_b) p2` for θ<0, `(przz_c (|θ|/π)^przz_power + przz_d) p2` (the page prints "θ < 0" for both branches, which is a typo in the source), `(przz_b + przz_d) 0.5` at θ=0; "This is normalized so that θ=π/2 gives the 2-qubit fault probability (p2)."
- SPAM: `p_meas` "Either a float or a tuple of 2 floats ... the first element is the probability a bit flip is applied if a 0 result occurs during measurement while the second error rate if a 1 is measured"; `p_init`; crosstalk `p_crosstalk_meas`, `p_crosstalk_init`.
- Memory: "The noise model includes a memory error for which Z is applied. This is often called 'dephasing' or 'memory' noise and depends on the duration for which the qubits are idling or transporting in the trap." Quadratic (coherent RZ for statevector, incoherent Pauli-Z with `coherent_to_incoherent_factor` for stabilizer) plus linear dephasing, "transport_dephasing" and "idle_dephasing" both on by default.
- Leakage: "The Helios emulators incorporate leakage noise with default error parameters that are also user specifiable. This is not included in H2 emulators." (Leakage enters H2 only through the spontaneous-emission branch above.)
- Scaling knobs: `scale`, `p1_scale`, `p2_scale`, ... "All the errors are applied even when only certain parameters are specified. Only the parameters specified are overridden. To turn off certain error parameters, explicitly set them to 0."
- Caveat: "When deviating from the default emulation model, users should not assume that performance predicted with modified error parameters will match hardware performance."

[F] These parameters are what `options={"error_params": {...}}` in aqora / `QuantinuumConfig.error_params` in Nexus override (section 1.6).

### 3.3 H2-2E default parameters (published)

[F] https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/emulators/h2_emulators.html, table "H2-2E" (the sub-heading in the HTML source reads "H2-1E emulators from 2025-07-16" under both the H2-1E and H2-2E tables; the H2-2E column header itself reads "H2-2E"):

| parameter | H2-2E default | H2-1E default (same page) |
|---|---|---|
| Qubits (Statevector) / (Stabilizer) | 32 / 56 | 32 / 56 |
| Connectivity; parallel 2-qubit ops; Wasm | all-to-all; 4; True | same |
| 1-Qubit Fault Probability (p1) | 7.3e-05 | 1.89e-05 |
| 2-Qubit Fault Probability (p2) | 0.00129 | 0.00105 |
| Bit-Flip Measurement Probability, 0 outcome (p_meas) | 0.0009 | 0.0006 |
| Bit-Flip Measurement Probability, 1 outcome (p_meas) | 0.0018 | 0.00139 |
| Crosstalk Measurement Fault Probability (p_crosstalk_meas) | 8.8e-06 | 3.3e-06 |
| Initialization Fault Probability (p_init) | 4e-05 | 4e-05 |
| Crosstalk Initialization Probability (p_crosstalk_init) | 9.6e-06 | 3.3e-06 |
| p1_emission_ratio | 0.32 | 0.54 |
| p2_emission_ratio | 0.59 | 0.255 |
| quadratic_dephasing_rate | 0.043 | 0.043 |
| linear_dephasing_rate | 0.0028 | 0.0028 |
| coherent_to_incoherent_factor | 2.0 | 2.0 |
| przz_a, przz_b, przz_c, przz_d, przz_power | 1.518, 0.241, 1.518, 0.241, 1.0 | same |

[F] Same page: "Because of the memory requirements, a slowdown in the number of Hardware Quantum Credits (HQCs) processed in an hour is observed for state vector emulations using 25 qubits or more. ... It is generally recommended that users perform state vector emulations with less than 28 qubits." and "In comparing the H2 emulation to H2 quantum computer results, users may experience a larger discrepancy than experienced comparing System Model H1 emulators to H1 quantum computers."

### 3.4 HQC formula

[F] https://docs.quantinuum.com/systems/trainings/helios/getting_started/costing.html, equation (1):

HQC = 5 + (C / 5000) ( Max(N_1q) + 10 Max(N_2q) + 5 Max(N_M) )

with "C: Number of shots required to run the program on hardware; Max(N_1q): The maximum number of physical 1-qubit gates from a specific shot instance over the 10 shot simulation (R_z operations excluded), hence the number of R_xy (phased_x) gates; Max(N_2q) The maximum number of physical 2-qubit gates ... hence the number of R_zz (zz_phase) gates; Max(N_M) The maximum number of measure (measure), leakage measurement (leaked_measure), resets (measure_and_reset) or initializations (maximum ion allocations)". The page calls it "Quantinuum's HQC formula".

[O] This page is the Helios costing page; for a static H2 circuit the "Max over 10 shots" collapses to the gate counts of the compiled circuit, i.e. HQC = 5 + C (N_1q + 10 N_2q + 5 N_M)/5000. No H2-specific page on docs.quantinuum.com restates the formula (searched: hardware user guide H2 page, access page, emulator pages, data sheet). Treat the H2 form as inferred until the H2-2SC syntax checker returns a cost.

[F] H2 limits, https://docs.quantinuum.com/systems/user_guide/hardware_user_guide/h2.html: "Each shot submitted to hardware has a 50 HQC hard limit. Each job submitted to hardware is limited to 10,000 shots (500,000 HQC hard limit)."

[F] Syntax checker, https://docs.quantinuum.com/systems/user_guide/hardware_user_guide/access.html: "If the code compiles, the syntax checker will return a completed status, the cost of the circuit in Hardware Quantum Credits (HQCs), and results of all (0, 0, ..., 0). Submission to the syntax checker does not incur a HQC cost."

### 3.5 Selene, local

[F] https://docs.quantinuum.com/selene/: "Quantinuum's emulation framework for hybrid programs." "Selene is an open-source project built in Rust with Python bindings" (https://github.com/quantinuum/selene). User guide: https://docs.quantinuum.com/selene/user_guide/overview.html.

[F] Install test here: `NO_PROXY= no_proxy= pip install --break-system-packages selene-sim guppylang` succeeded with no dependency conflict: "Successfully installed guppylang-1.1.2 guppylang-internals-1.1.2 lief-0.17.6 pydot-4.0.1 selene-core-0.3.2 selene-hugr-qis-compiler-0.5.0 selene-sim-0.3.4 tket-0.15.10 tket-eccs-0.6.0 tket-exts-0.14.3 types-tqdm-4.70.0.20260906 wasmtime-48.0.0 ziglang-0.16.0" (pytket 2.18.4, pytket-quantinuum 0.59.3, qnexus 0.51.1, aqora 0.35.1 left untouched).

[F] Bell state run locally with every proxy variable unset (`HTTPS_PROXY= https_proxy= HTTP_PROXY= http_proxy= python3 ...`), guppy route, 1000 shots: `counts: {'11': 521, '00': 479}`. Code:

```python
from collections import Counter
from guppylang import guppy
from guppylang.std.builtins import result
from guppylang.std.quantum import cx, h, measure, qubit
from selene_sim import build, Quest

@guppy
def bell() -> None:
    q0, q1 = qubit(), qubit()
    h(q0); cx(q0, q1)
    result("c0", measure(q0).read())   # guppylang 1.1.2: measure() returns a Measurement; .read() gives bool
    result("c1", measure(q1).read())

runner = build(bell.compile())
counts = Counter()
for shot in runner.run_shots(Quest(), n_qubits=2, n_shots=1000):
    d = dict(shot); counts[f"{int(d['c0'])}{int(d['c1'])}"] += 1
print(counts)
```

[F] pytket route (pytket `Circuit` loaded into guppy with `guppy.load_pytket`), same conditions: `pytket->guppy->Selene counts: {'11': 514, '00': 486}`. Code:

```python
from collections import Counter
from pytket import Circuit
from guppylang import guppy
from guppylang.std.builtins import array, result
from guppylang.std.quantum import qubit, discard_array
from selene_sim import build, Quest

circ = Circuit(2, 2); circ.H(0).CX(0, 1).measure_all()
bell_pytket = guppy.load_pytket("bell_pytket", circ)   # signature array[qubit, 2] -> array[bool, 2]

@guppy
def main() -> None:
    qs = array(qubit() for _ in range(2))
    c = bell_pytket(qs)
    discard_array(qs)            # required: qubits are linear and must be consumed
    result("c", c)

runner = build(main.compile())
counts = Counter()
for shot in runner.run_shots(Quest(), n_qubits=2, n_shots=1000):
    counts["".join(str(int(b)) for b in dict(shot)["c"])] += 1
print(counts)
```

[F] `selene_sim` 0.3.4 exports (from `dir(selene_sim)`): simulators `Quest`, `Stim`, `Coinflip`, `ClassicalReplay`, `QuantumReplay`; error models `IdealErrorModel`, `DepolarizingErrorModel`, `SimpleLeakageErrorModel`; runtimes `SimpleRuntime`, `SoftRZRuntime`; `HeliosInterface`, `MetricStore`, `build`. [O] No H2 noise model ships with selene-sim; the local noise proxy has to be `DepolarizingErrorModel` with the H2-2E `p1`/`p2`/`p_meas` numbers above, which omits dephasing/memory and the angle scaling.

[F] Nexus also hosts a `Selene` platform (aqora `nexus:Selene`, maxQubits 26, inputs HUGR_V1/QIR_V1); the aqora quick start uses it. The local package does not need the network: the Bell runs above succeeded with proxies unset.

---

## 4. H2 data sheet and H2-2 numbers

[F] Data sheet: https://docs.quantinuum.com/systems/_static/assets/data_sheets/Quantinuum%20H2%20Product%20Data%20Sheet.pdf, "Version 4.00 September 17, 2025" (364,004 bytes, 4 pages). It covers the generation, not individual machines: "Product data sheets are provided per generation of quantum computers" (performance_validation page). Table 1 (Typical | Max): "Qubits 56; Connectivity All-to-all; Parallel two-qubit operations 4; 1-qubit gate infidelity 3 × 10−5 | 2 × 10−4; 2-qubit gate infidelity 1 × 10−3 | 2 × 10−3; State preparation and measurement (SPAM) error 1 × 10−3 | 5 × 10−3; Memory error per qubit at average depth-1 circuit 2 × 10−4 | 2 × 10−3; Mid-circuit measurement cross-talk error 5 × 10−6 | 2 × 10−4". The data sheet contains no HQC formula and no H2-2-specific column.

[F] No separate H2-2 data sheet exists on the docs site (only the H2 and Helios PDFs are linked from the access page). H2-2-specific numbers are on https://docs.quantinuum.com/systems/user_guide/hardware_user_guide/performance_validation.html, table "H2-2" (Infidelity | Uncertainty): "1-Qubit Gate Error 2.8e-05 | 3.6e-06; 1-Qubit Gate Leakage Error 6.1e-06 | 1.3e-06; 2-Qubit Gate Error 8.3e-04 | 4.8e-05; 2-Qubit Gate Leakage Error 1.9e-04 | 1.7e-05; Memory Error per Depth-1 Circuit Time 1.2e-04 | 2.0e-05; Measurement Crosstalk Error 2.2e-05 | 5.3e-07; SPAM Error (0) 6.7e-04 | 8.7e-05; SPAM Error (1) 1.2e-03 | 1.1e-04". Definition on the same page: "The total N-qubit fidelity is calculated as F_T = F_RB + L/D, where D=1 (D=2)". The page does not print the measurement date of this table.

[F] Raw benchmark data: https://docs.quantinuum.com/systems/user_guide/hardware_user_guide/benchmarks/hardware_data.html lists H2-2 downloads dated 2025-08-28 ("Measurement_crosstalk.json", "SPAM.json", "SQ_RB.json", "TQ_RB.json", "Memory_RB.json") and the GitHub repository https://github.com/CQCL/quantinuum-hardware-specifications (performance_validation page: "Hardware Benchmarks GitHub Repository").

[O] Note the mismatch to keep in the report: the H2-2E emulator defaults (p2 = 1.29e-3, p1 = 7.3e-5, from the 2025-07-16 model) are worse than the H2-2 measured values on the performance page (2-qubit 8.3e-4, 1-qubit 2.8e-5), and H2-2E p1 is larger than H2-1E p1 while the hardware page shows H2-2 as the better machine. Quantinuum states "System Model H2 error models will mature over time." Quote both sets and say which one each number comes from.

---

## 5. Open items (not determinable without the user's credentials)

- The team organization's aqora username (`as_entity`) and whether the submitting account is Owner/Admin of it.
- The real challenge/track slugs, the active stage's `noCode` flag, `submissionPreamble`, scoring criteria weights, and whether a PDF attachment is requested on the submit form.
- The team's remaining HQC quota on H2-2E and the per-job cost cap ("Job cost exceeds allowed cost (code 1002)" reported by another participant); neither aqora's schema (`ProviderJob` has no cost field) nor the anonymous API exposes it.
- Whether `H2-Emulator` (Nexus tier) honours `noisy_simulation: False` in practice.
- Access-token lifetime for `Client.with_token`.
