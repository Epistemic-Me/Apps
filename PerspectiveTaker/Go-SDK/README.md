# Go-SDK
The Go SDK for Epistemic Me

### Creating an Instance of EpistemicMe client

Use the following code snippet to create an instance of the EpistemicMe client

```
import epistemicme "github.com/EpistemicMe/Go-SDK"

// Create a new client
epistemicme := epistemicme.New("https://localhost:8080")
```

### Creating a Dialectic    

```
dialectic, err := epistemicme.NewDialectic(ctx, "sf_123")
if err != nil {
    log.Fatal(err)
}

if dialectic.HasQuestion() {        
    fmt.Println(dialectic.GetQuestion().Text)
    // Question: How important is drinking water to your health?
}

// Answer to the question
dialectic.Answer(ctx, "Drinking water is very important to my health")

```
