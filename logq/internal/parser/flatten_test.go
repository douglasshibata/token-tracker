package parser

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

func testFlatten(t *testing.T) {
	entry := map[string]interface{}{
		"user": map[string]interface{}{
			"id": "123",
			"details": map[string]interface{}{
				"email": "test@example.com",
			},
		},
		"model": "gpt-4",
	}

	flat := Flatten(entry)
	assert.Equal(t, "123", flat["user_id"])
	assert.Equal(t, "test@example.com", flat["user_details_email"])
	assert.Equal(t, "gpt-4", flat["model"])
}

func TestGetValue(t *testing.T) {
	entry := map[string]interface{}{
		"usage": map[string]interface{}{
			"total_tokens": 100,
		},
	}

	val := GetValue(entry, "usage.total_tokens")
	assert.Equal(t, 100, val)

	val = GetValue(entry, "non.existent")
	assert.Nil(t, val)
}
