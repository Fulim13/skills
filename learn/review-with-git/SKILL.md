---
name: review-with-git
description: 'Grade the practice branch against the reference solution on main'
disable-model-invocation: true
---

Counterpart to [build-review-with-git](../build-review-with-git/SKILL.md). That skill
hides a solution and leaves a practice branch; this one grades the attempt on that
branch against the solution that stayed on `main`.

The verdict is about **functionality**, not text. Different names, different helper
split, different loop shape — all fine if the behaviour matches what the instructions
asked for. Only behaviour differences fail.

# Resolve the three inputs

1. **Practice branch** — `HEAD`, expected to be named `<Chapter_Number>_<Lesson_Slug>`.
   If `HEAD` is `main` or the name doesn't match, ask the user which branch to grade.
2. **Lesson commit** — the commit on `main` whose message starts with the chapter
   number:

   ```sh
   git log main --oneline --grep="^<Chapter_Number>:"
   ```

   Call it `<sha>`. If zero or several match, ask the user for the SHA.

3. **Branch point** — `git merge-base main HEAD`. Confirm it equals `<sha>^`; if it
   doesn't, the branch was cut somewhere else — say so and ask before continuing.

Then read all three:

```sh
git show <sha>                          # reference solution
git diff <sha>^ HEAD -- . ':!instructions'   # the attempt
git show HEAD:instructions/<Chapter_Number>_<Lesson_Slug>.md   # the ask
```

An empty attempt diff means nothing was submitted — report that and stop.

# Grade

1. EXPLORE the repository, and read the files both diffs touch plus their direct
   dependencies. A handler can be correct in isolation and unreachable because the
   route was never registered.
2. Walk the instruction file's numbered tasks **in order**. Each one is either done,
   partially done, or missing — anchor every finding to its step number.
3. Where the attempt diverges from the reference, decide which bucket it lands in:
   - **Equivalent** — different code, same observable behaviour. Not a finding.
   - **Blocking** — wrong or missing behaviour: a task not done, a logic error, code
     that doesn't compile, a wrong literal that changes behaviour (status code, limit,
     duration, error string, default), a missing route/registration/migration.
   - **Note** — behaviour is right but it departs from the instructions: a different
     identifier than the one specified, logic in a different file, a skipped
     verification step, an obvious simplification left on the table.
4. **Run the code.** Don't grade by eye alone. Use whatever the repo provides —
   `go build ./...`, `go test ./...`, `npm test`, `make` — and, if the instruction
   file ends with a verification step (it should), run that exact command and compare
   against its expected output. Report what you ran and what happened.
5. **Theory questions.** If the instruction file has a `# Theory Questions` section,
   or the reference diff has `// Question:` / `// Answer:` comments, check the
   attempt's answers for correctness too. A wrong answer is a Note, not a Blocker,
   unless the code it governs is also wrong.

# Verdict

Exactly one of:

- **PASS** — every task done, behaviour matches, build and verification green.
- **PASS WITH NOTES** — behaviour matches, but Notes exist.
- **FAIL** — one or more Blockers.

# Report

```
## <Chapter_Number>: <Lesson_Title>
Verdict: FAIL

Verification
- `go build ./...` — ok
- `curl -i -d "$BODY" localhost:4000/v1/movies` — got 200 OK, expected 201 Created

Blocking
1. Step 2.1 — `snippetCreatePost` is registered with `mux.HandleFunc("/snippet/create")`,
   so it also answers GET. The step asked for `POST /snippet/create`.
   Hint: the method belongs in the pattern string.

Notes
1. Step 1.2 — named `writeJson()`; the step specified `writeJSON()`.

Done
- Step 1, Step 3.
```

Two rules on the report:

- **Lead with the hint, not the answer.** For each Blocker, point at the file and line
  and name the shortfall, then give one nudge. The whole point of the practice branch
  is recall, and pasting `git show <sha>` spends it. Offer the reference at the end —
  *"Say `show solution` for the reference diff"* — and only paste it when asked, or
  when the same Blocker survives a second review.
- **Say `Done` out loud.** List the steps that passed. A review that only enumerates
  faults is hard to learn from.

After a FAIL, the user fixes the branch and reruns this skill; nothing is committed or
merged by the review itself.
