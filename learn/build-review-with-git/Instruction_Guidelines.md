# Core Principle

The respondent should spend 100% of their thinking on **how to implement**, and 0% on **what to name things, where to put them, or what values to use**.

# Guidelines

1. **No solution section.** The lesson commit's git diff is the answer key. Everything the respondent needs must live in the steps

2. **Write the question as an imperative numbered task list**, one action per step, with nested sub-steps for detail.

   ```
   1. Update the `Insert()` method in `internal/data/movies.go`
       1. Define the SQL query for inserting a new record and returning system-generated data
           1. INSERT title, year, runtime, genres
           2. RETURN id, created_at, version
       2. Create an args slice containing the values for the placeholder parameters
   ```

3. **Always define every name for the respondent.** Function names, method names, struct names, field names, variable names, receiver types, file names, route names, migration names. Never make them invent an identifier.
   - ✅ "Create a reusable `writeJSON()` helper method"
   - ❌ "Create a helper to write JSON"

4. **Always give the exact file path** the code goes into, either in the step (`in cmd/api/helpers.go`) or as a `File: cmd/api/helpers.go` header line above the code block in the solution.

5. **Always spell out the signature** — parameter names, parameter types, and return types.

   ```
   - Parameters: `http.ResponseWriter`, HTTP status code (`int`), data (`any`), additional headers (`http.Header`)
   - Return: `error`
   ```

6. **Always give the exact literal values.** Never let the respondent guess a number or string:
   - numbers/limits — `2 requests per second`, `burst of 4`, `1_048_576`, `500 bytes`, `10,000,000`
   - durations — `3-second context`, `15 minutes`, `30-second timeout`, `500 ms retry, 3 times`
   - defaults — `Page` default `1`, `PageSize` default `20`, `Sort` default `id`
   - CLI flag names — `-limiter-burst`, `-db-max-open-conns`, `smtp-host`
   - error message strings — `"record not found"`, `"rate limit exceeded"`, `"must be a valid email address"`
   - HTTP status codes — `201 Created`, `422 Unprocessable Entity`, `429 Too Many Requests`

7. **Always give setup/dependency instructions as their own step**, and show the exact command in the solution. The respondent must never have to look up an install command.
   Install the rate limiting package

   ```bash
   go get golang.org/x/time/rate@latest
   migrate create ...
   go mod init ...
   ```

8. **Give the data setup, not just the query.** If a task needs rows in the DB or a specific app state, supply the exact `curl`/`BODY='...'`/SQL that creates it.

9. **End every practical block with a verification step**, and put the exact verification command _and its expected output_ in the solution.
   Run the comamnd to verify the output

   ```bash
   BODY='{"title":"Moana","year":2016,...}'
   curl -i -d "$BODY" localhost:4000/v1/movies
   ```

   Output:

   ```
   HTTP/1.1 201 Created
   Content-Type: application/json
   Location: /v1/movies/1
   ```
