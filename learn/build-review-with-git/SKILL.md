---
name: build-review-with-git
description: 'Turn the current git changes into a review lesson'
disable-model-invocation: true
---

### Naming

1. **Lesson_Title** - use the user's provided lesson title or derive one from the diff
2. **Chapter_Number** - use the user's provided chapter number or Continue from the highes number already in `./instructions/`
3. - **Lesson_Slug** — lowercase title, words joined by `-`.

# Steps

1. EXPLORE the whole repository.
2. READ the diff (`git diff` and `git diff --staged`), then read the files it
   touches and their direct dependencies.
3. Write the instructions based on [Instruction Guidelines](./Instruction_Guidelines.md).
4. Show to the user and revise until approved.
5. **Theory questions (optional).** If the diff includes theory questions:
   1. Keep them in the code as comments:
      ```
      // Question: What is ...?
      // Answer: My answer is ...
      ```
   2. Also add a `# Theory Questions` section to `instructions/<Chapter_Number>_<Lesson_Slug>.md`:

      ```
      # Theory Questions

      Q1: <question>
      Answer: <answer>
      ```

6. Save to `instructions/<Chapter_Number>_<Lesson_Slug>.md`. 7. Commit on the current branch:

```sh
git add .
git commit -m "<Chapter_Number>: <Lesson_Title>"
```

6. Create the practice branch from the commit before the lesson, so the code
   changes are absent but the lesson survives. Note the SHA from step 5 and
   substitute it below:

```
git switch -c <Chapter_Number>_<Lesson_Slug> <sha>^
git restore --source=<sha> -- instructions/<Chapter_Number>_<Lesson_Slug>.md
```

7. Commit:

```
git add .
git commit -m "practice: <Chapter_Number> <Lesson_Title>"
```
