Given the code changes of these:

```go
package main

import (
	"fmt"
	"log"
	"net/http"
	"strconv"
)

func home(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("Hello from Snippetbox"))
}

func snippetView(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.Atoi(r.PathValue("id"))

	if err != nil || id < 1 {
		w.WriteHeader(http.StatusNotFound)
		return
	}

	msg := fmt.Sprintf("Display a specific snippet %d", id)

	w.Write([]byte(msg))
}

func snippetCreate(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("Display a form for creating a new snippet"))
}

func snippetCreatePost(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("Save a new snippet"))
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", home)
	mux.HandleFunc("GET /snippet/view/{id}", snippetView)
	mux.HandleFunc("GET /snippet/create", snippetCreate)
	mux.HandleFunc("POST /snippet/create", snippetCreatePost)

	log.Println("The server is starting on port 4000")

	err := http.ListenAndServe(":4000", mux)
	log.Fatal(err)
}
```

This is the example instruction build:
| Route pattern | Handler | Action |
| -------------------- | ----------------- | ----------------------------------------- |
| /{$} | home | Display the home page |
| /snippet/view/{id} | snippetView | Display a specific snippet |
| /snippet/create | snippetCreate | Display a form for creating a new snippet |
| /snippet/create | snippetCreatePost | Save a new snippet |

1. Restrict all three routes to acting on `GET` requests

2. Create a new route that `snippet/create` that support `POST` request only
