package epistemicme

import (
	"context"
	"time"

	"connectrpc.com/connect"
	internal "github.com/EpistemicMe/Go-SDK/internal"
	"github.com/EpistemicMe/Go-SDK/internal/pb"
	"github.com/EpistemicMe/Go-SDK/internal/pb/models"
)

type Dialectic struct {
	ID               string
	CreatedAt        time.Time
	UpdatedAt        time.Time
	UserInteractions []*UserInteraction

	client *internal.DialecticService
}

type Answer struct {
	Text      string
	CreatedAt int64
}

// Question represents a question asked by the agent
type Question struct {
	Text      string
	CreatedAt int64
}

type UserInteraction struct {
	ID        string    `json:"id"`
	Answer    string    `json:"answer"`
	Question  *Question `json:"question"`
	Status    string    `json:"status"`
	Type      string    `json:"type"`
	UpdatedAt int64     `json:"updatedAtMillisUtc"`
}

// New creates a new dialectic for the given self model ID
func (e *EpistemicMe) NewDialectic(ctx context.Context, selfModelID string) (*Dialectic, error) {
	req := connect.NewRequest(&pb.CreateDialecticRequest{
		SelfModelId: selfModelID,
	})

	resp, err := e.client.CreateDialectic(ctx, req)
	if err != nil {
		return nil, err
	}

	return &Dialectic{
		ID:               resp.Msg.Dialectic.Id,
		CreatedAt:        time.UnixMilli(resp.Msg.Dialectic.CreatedAtMillisUtc),
		UpdatedAt:        time.UnixMilli(resp.Msg.Dialectic.UpdatedAtMillisUtc),
		UserInteractions: convertPBInteractionsToModel(resp.Msg.Dialectic),
		client:           s,
	}, nil
}

// Answer adds a new answer to the dialectic
func (d *Dialectic) Answer(ctx context.Context, selfModelID string, answer string) error {
	req := connect.NewRequest(&pb.UpdateDialecticRequest{
		Id:          d.ID,
		SelfModelId: selfModelID,
		Answer: &models.UserAnswer{
			UserAnswer:         answer,
			CreatedAtMillisUtc: time.Now().UnixMilli(),
		},
	})

	resp, err := d.client.client.UpdateDialectic(ctx, req)
	if err != nil {
		return err
	}

	// Update local state with response
	d.UpdatedAt = time.UnixMilli(resp.Msg.Dialectic.UpdatedAtMillisUtc)
	d.UserInteractions = convertPBInteractionsToModel(resp.Msg.Dialectic)

	return nil
}

// GetQuestion returns the current question if one exists
func (d *Dialectic) GetQuestion() *Question {
	if len(d.UserInteractions) == 0 || !d.HasQuestion() {
		return nil
	}

	lastInteraction := d.UserInteractions[len(d.UserInteractions)-1]
	return lastInteraction.Question
}

// HasQuestion returns true if there is a current question that hasn't been answered
func (d *Dialectic) HasQuestion() bool {
	if len(d.UserInteractions) == 0 {
		return false
	}

	lastInteraction := d.UserInteractions[len(d.UserInteractions)-1]
	return lastInteraction.Question != nil && lastInteraction.Answer == ""
}

// Helper function for converting protobuf interactions to model
func convertPBInteractionsToModel(pbDialectic *models.Dialectic) []*UserInteraction {
	interactions := make([]*UserInteraction, len(pbDialectic.UserInteractions))
	for i, interaction := range pbDialectic.UserInteractions {
		qa := interaction.GetQuestionAnswer()

		var question *Question
		if qa.Question != nil {
			question = &Question{
				Text:      qa.Question.Question,
				CreatedAt: qa.Question.CreatedAtMillisUtc,
			}
		}

		interactions[i] = &UserInteraction{
			ID:        interaction.Id,
			Answer:    qa.Answer.UserAnswer,
			Question:  question,
			Status:    string(interaction.Status),
			Type:      string(interaction.Type),
			UpdatedAt: qa.UpdatedAtMillisUtc,
		}
	}
	return interactions
}
