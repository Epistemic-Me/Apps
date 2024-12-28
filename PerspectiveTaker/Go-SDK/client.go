package epistemicme

import (
	"net/http"

	pbconnect "github.com/EpistemicMe/Go-SDK/internal/pb/pbconnect"
)

type EpistemicMe struct {
	client pbconnect.EpistemicMeServiceClient
}

func New(baseURL string) *EpistemicMe {
	client := pbconnect.NewEpistemicMeServiceClient(http.DefaultClient, baseURL)
	return &EpistemicMe{
		client: client,
	}
}
