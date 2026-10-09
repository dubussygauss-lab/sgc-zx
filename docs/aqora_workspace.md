# Aqora workspace: CLI/API capabilities and publish procedure (read-only investigation, 2026-10-09)

Nothing was created, uploaded, published or submitted. No authenticated call was made. Sources: installed `aqora` 0.35.1 (`/usr/local/lib/python3.13/dist-packages/aqora/`), `aqora <cmd> --help`, GraphQL operation strings embedded in `aqora/_aqora.abi3.so`, anonymous GraphQL introspection of `https://aqora.io/graphql`, the CLI source on GitHub (`https://github.com/aqora-io/cli`, HEAD be39e44 = v0.36.0, 2026-10-08), and `https://docs.aqora.io/llms-full.txt`.

## 1. Workspace commands in aqora 0.35.1

- [F] `aqora --help` lists: install, new, model, job, pair, login, auth, python, shell, store, test, upload, template, clean, add, remove, lab. There is no workspace create, clone, push, publish or submit command.
- [F] `aqora new` has only `use-case`. `aqora upload [COMPETITION]` and `aqora template <COMPETITION>` drive the code-competition route (`createSubmissionVersion` with a `pyproject.toml` that has `[tool.aqora]`), not workspaces. The track is `noCode: true` (docs/rubric.md), so this route does not apply [O].
- [F] `aqora pair <owner/slug[@version]>` attaches a local agent (Claude Code, Codex, opencode) to the editor runner of an existing draft workspace version. It does not upload files or publish. It fails with "The version has no editor runner. Open the workspace on aqora.io to start" when no runner is live (GitHub `src/commands/pair/target.rs`).
- [F] The only workspace operations the 0.35.1 binary contains are reads: `GetWorkspaceNotebookDownloadUrl`, `GetWorkspaceVersionNotebookDownloadUrl` (used by `aqora.notebook.load("owner/slug", ...)`, which downloads and imports a workspace notebook) and the `*PairEditor` queries.
- [F] GitHub HEAD v0.36.0 adds no workspace command either (`src/commands/mod.rs`).
- [F] The server API has the full set (live introspection, mutation descriptions quoted):
  - `createWorkspace(input: {name!, private!, shortDescription, pythonRuntime: UV|CONDA, fromVersionId}, asEntity)`: "Create a workspace with a first draft version 0.0.0, seeded from the template or from `input.fromVersionId`."
  - `cloneWorkspaceVersion(id!, input: {slug, version, competitionId, private}, asEntity)`. With `competitionId`, "the clone's owner is forced to the viewer's team for the track".
  - `createWorkspaceVersion(id!, input: {version!, fromVersionId})`: "Create a new draft version of a workspace."
  - `initWorkspaceVersionFileUpload(id!, input: {filename!, contentType!, contentLength!})`: "PUT the file to `uploadUrl`, then import it with `importWorkspaceVersionFile`."
  - `importWorkspaceVersionFile(id!, input: {key!, path!, convert!})`. `convert: true` turns `.ipynb/.md/.qmd/.py` into a marimo notebook. Progress via subscription `workspaceImportStatus(id)`. One file per call.
  - `updateWorkspaceVersion(id!, input: {version, overviewNotebook, libNotebook})`.
  - `publishWorkspaceVersion(id!)`: "Publish a draft version. It becomes read-only and viewable through its `renderer`."
  - `setSubmissionWorkspaceVersions(competitionId!, workspaceVersionIds!, asEntity)`: "Replace the set of published workspace versions linked to the viewer's (team's) submission for a simple/no-code competition."
  - `uploadNoCodeSubmissionVersion(competitionId!, input: {files: [Upload!]!}, asEntity)`: "Submit files for a "no-code" competition."
- [F] These mutations are reachable only by raw GraphQL: `aqora.Client().send(query, **vars)` in Python (`_aqora.pyi`) or the aqora MCP server `https://aqora.io/mcp` (tool `run_graphql`, docs: "can do everything your account can, including possibly non-reversible actions").
- [O] "Publish" and "Submit to Track" in the organisers' PDF are the web-UI buttons for `publishWorkspaceVersion` and `setSubmissionWorkspaceVersions`. Using the web UI is safer than scripting these mutations.

## 2. What a workspace must contain

- [F] A new workspace is scaffolded with exactly `readme.py`, `.ignore`, `.secrets`, and no `pyproject.toml` (GitHub `template/src/workspace.rs`, test `renders_the_starter_files`: "No `pyproject.toml`: kernels run in a per-notebook environment, built by uv or pixi ... from readme.py's own PEP 723 header"). The same template text is embedded in the 0.35.1 binary (`workspace/readme.py.hbs`).
- [F] `readme.py` is a marimo notebook and "the platform picks it as a workspace's default overview notebook by exact filename" (same file, test comment). Default header pins `requires-python = "==3.12.*"`, dependency `marimo` unpinned.
- [F] The overview notebook can be overridden per version (`UpdateWorkspaceVersionInput.overviewNotebook`). `WorkspaceVersion.overviewNotebook` is "this version's override if set, else the auto-detected default".
- [F] No `[tool.aqora]` section is needed for a workspace. `[tool.aqora]` and the case-insensitive `README.md`/`readme.txt` lookup (`src/readme.rs`) belong to `aqora upload`, the code-competition route.
- [F] Dependencies are declared in the notebook's PEP 723 header. `report/notebook_skeleton.py` already has one (`requires-python = ">=3.12"`, aqora 0.35.1, pytket 2.18.4, pytket-quantinuum 0.59.3, pyzx 0.10.7, pandas, matplotlib).
- Unverifiable: the cause of `{"detail":"file readme.md not found"}` in the organisers' screenshot. Nothing in the CLI source or the public schema references a workspace `readme.md`. [O] The likeliest reading is that the challenge template version sets its overview notebook to `readme.md` (marimo accepts `.md` notebooks) and the file was missing in that preview. Check the cloned workspace's file list before relying on either name.
- [O] Safe layout: keep whatever overview notebook the challenge clone has, add our notebook at the workspace root as `readme.py` (or set it as overview notebook), add `README.md` for the checklist's "README with instructions", and put `results/`, `pipelines/`, `report/`, `submit/` beside it. The notebook's `_find_root()` already accepts a notebook sitting next to `results/` (lines 103-118).

## 3. Can we tell read-only whether `<username>/sg-grand-challenge` exists?

- [F] A pure read exists: `workspaceBySlug(owner, slug)` ("null when absent or not readable"), `workspaces(filters)` ("workspaces the viewer can read"), and `Competition.viewerWorkspace` ("The viewer's team's most recent workspace cloned from this track's templates").
- [F] The challenge is private: anonymous `competitionBySlug("quantinuum-sg-grand-challenge")` returns null (docs/platform_notes.md 2.1). An anonymous query cannot see a private workspace.
- [F] The stored access token expired at 2026-10-08T18:57:54Z (`expires_at` field of `/home/claude/aqora-home/credentials.json`, secrets not read out). Any authenticated call, including `aqora auth token` and `Client().send(...)`, first runs `Oauth2RefreshMutation`, which issues a new refresh token and rewrites the credentials file (GitHub `src/credentials.rs`, `refresh_credentials`, lines 93-135).
- [O] That refresh is a server-side state change, and it may invalidate the refresh token in Kam's Mac copy. I therefore ran no authenticated command. The check needs Kam's approval, or Kam can open the workspace list on aqora.io himself.
- [O] If approved, the minimal query is `{ viewer { username } w1: workspaceBySlug(owner: "learned_zx_rewriting", slug: "sg-grand-challenge") { id private latestVersion { version publishedAt overviewNotebook } } }`, plus the same with Kam's username. The team org is the likely owner because a track clone's owner "is forced to the viewer's team".

## 4. Shortest procedure (for Kam, or for us after 「可以」)

[O] The web UI is the only route that needs no new scripting, and the CLI has no upload or publish command.

1. On aqora.io, open the challenge's track page and open the existing workspace `<owner>/sg-grand-challenge`. If none exists, clone the track template from the track page. The owner then becomes the team.
2. Open the latest draft version in the marimo editor. If only published versions exist, create a new draft version.
3. Upload `submission/code.zip` with the marimo file panel. [O] Uploading 2483 files one by one is impractical. Unzip it in a scratch cell: `import shutil; shutil.unpack_archive("code.zip", ".")`, then delete that cell and `code.zip`. Unverifiable: that the marimo file panel in aqora workspaces accepts uploads. If it does not, upload the zip through `initWorkspaceVersionFileUpload` and `importWorkspaceVersionFile` (`convert: false`), which needs 「可以」.
4. Copy `report/notebook_skeleton.py` to the workspace root as `readme.py`, or set it as overview notebook. Keep `README.md` at the root. Run it once in the editor to confirm the PEP 723 environment builds. Python is 3.12 there.
5. Click **Publish**.
6. Click **Submit to Track**, or on the direct submission page (`https://aqora.io/challenges/quantinuum-sg-grand-challenge/tracks/quantinuum-sg-grand-challenge/submission`) upload the files and select the published workspace version to link (`setSubmissionWorkspaceVersions`).
7. Confirm the submission confirmation is shown. Re-publish and re-submit after any later change ("Only the latest submission will be evaluated", organisers' PDF p. 4).

- Unverifiable: whether a file upload on the direct page and a workspace link replace each other or coexist. [O] Do both in one sitting, then check that the submission page shows the files and the linked version together.
