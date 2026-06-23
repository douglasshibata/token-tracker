package parser

import (
	"fmt"
	"strings"
)

func Flatten(entry map[string]interface{}) map[string]interface{} {
	flat := make(map[string]interface{})
	flatten("", entry, flat)
	return flat
}

func flatten(prefix string, entry interface{}, flat map[string]interface{}) {
	switch m := entry.(type) {
	case map[string]interface{}:
		for k, v := range m {
			newKey := k
			if prefix != "" {
				newKey = prefix + "_" + k
			}
			flatten(newKey, v, flat)
		}
	case []interface{}:
		// Handle arrays if needed, for now just store first element or stringify
		flat[prefix] = fmt.Sprintf("%v", m)
	default:
		flat[prefix] = m
	}
}

func GetValue(entry map[string]interface{}, path string) interface{} {
	// Support dot-notation access
	parts := strings.Split(path, ".")
	var current interface{} = entry
	for _, part := range parts {
		if m, ok := current.(map[string]interface{}); ok {
			current = m[part]
		} else {
			return nil
		}
	}
	return current
}
