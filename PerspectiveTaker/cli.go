package perspective_taker

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func main() {
	reader := bufio.NewReader(os.Stdin)
	fmt.Println("Perspective Taker CLI")
	fmt.Println("Type 'help' for available commands or 'exit' to quit")

	for {
		fmt.Print("Enter command: ")
		input, err := reader.ReadString('\n')
		if err != nil {
			fmt.Println("Failed to read input:", err)
			continue
		}

		input = strings.TrimSpace(input)
		args := strings.Split(input, " ")

		switch args[0] {
		case "exit":
			fmt.Println("Exiting CLI...")
			return
		case "help":
			displayHelp()
		case "list":
			listPerspectives()
		case "select":
			if len(args) < 3 {
				fmt.Println("Not enough arguments for select. Usage: select [perspective] [beliefMode]")
				continue
			}
			selectPerspective(args[1], args[2])
		case "dialogue":
			startDialogue()
			manageDialogue()
		case "summary":
			showSummary()
		default:
			fmt.Println("Unknown command:", args[0])
		}
	}
}

func displayHelp() {
	helpText := `
Available commands:
exit - Exit the CLI
help - Show this help message
list - List available perspectives
select [perspective] [beliefMode] - Select a perspective and belief mode
dialogue - Start and manage a dialogue
summary - Show summary of updated beliefs
`
	fmt.Println(helpText)
}

func listPerspectives() {
	fmt.Println("Listing available perspectives")
}

func selectPerspective(perspective, beliefMode string) {
	fmt.Printf("Selected perspective: %s with belief mode: %s\n", perspective, beliefMode)
}

func startDialogue() {
	fmt.Println("Starting dialogue...")
	startDialectic()
}

func manageDialogue() {
	reader := bufio.NewReader(os.Stdin)
	for {
		fmt.Print("Enter your response (type 'end' to finish dialogue): ")
		response, err := reader.ReadString('\n')
		if err != nil {
			fmt.Println("Failed to read input:", err)
			continue
		}

		response = strings.TrimSpace(response)
		if response == "end" {
			fmt.Println("Ending dialogue...")
			break
		}

		updateDialectic(response)
	}
}

func startDialectic() {
	fmt.Println("Dialectic session started. Here's your first question:")
	fmt.Println("What are your initial thoughts on the concept of personal identity?")
}

func updateDialectic(response string) {
	fmt.Printf("You answered: %s\n", response)
	fmt.Println("How does this relate to the continuity or change over time?")
}

func showSummary() {
	fmt.Println("Summary of updated beliefs:")
}
