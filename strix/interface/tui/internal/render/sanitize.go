package render

import "strings"

// ptrunc clamps a string to max runes-bytes-ish length, appending an ellipsis
// when it had to cut. Kept here (rather than in a renderer-specific file) so
// every tool renderer can share the same truncation behaviour.
func ptrunc(s string, max int) string {
	if len(s) > max {
		return s[:max-3] + "..."
	}
	return s
}

// psanitize flattens whitespace (newlines/tabs/carriage returns) in a single
// line of tool output and then truncates it.
func psanitize(s string, max int) string {
	clean := strings.NewReplacer("\n", " ", "\r", "", "\t", " ").Replace(s)
	return ptrunc(clean, max)
}
