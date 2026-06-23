# `logq` — High-Performance AI Log Analyzer

`logq` is a blindingly fast CLI tool specifically designed to query and aggregate LLM gateway traffic logs stored in `.jsonl` format. Unlike general-purpose tools, `logq` understands the shape of AI data and processes gigabytes of logs with minimal memory footprint.

## 🚀 Key Features

- **Streaming Pipeline:** Never loads the whole file into RAM. Processes line-by-line using buffered readers.
- **Auto-Flattening:** Automatically flattens nested LLM JSON structures (e.g., `usage.input_tokens` → `input_tokens`) for easy querying.
- **PII Awareness:** Built-in regex passing to redact API keys and sensitive user data in the terminal.
- **Math Engine:** Calculate sums, averages, and P99 latencies directly from the CLI.

## 🛠️ Technologies

- **Go 1.24:** Core language for peak performance and static binary distribution.
- **Cobra:** Robust CLI framework for flags and command management.
- **Sonic:** Blazing fast JSON library by ByteDance that bypasses standard reflection.
- **Lipgloss & Tablewriter:** Beautiful, color-coded terminal tables and UI elements.
- **hpcloud/tail:** Robust file tailing for live monitoring.

## 📁 Project Structure

```
logq/
├── cmd/                # Cobra command implementations (search, aggregate, etc.)
├── internal/
│   ├── processor/      # Core streaming line reader logic
│   └── parser/         # JSON flattening and dot-notation access
├── main.go             # Application entry point
└── Dockerfile          # Multi-stage build for minimal production image
```

## 💻 How to Use

### 1. Build
```bash
go build -o logq
```

### 2. Search
Find all expensive requests (cost > 0.10) for a specific model:
```bash
./logq search logs.jsonl --filter "model=claude-3-opus" --columns user_id,model,total_cost
```

### 3. Aggregate
Calculate total spend grouped by department:
```bash
./logq aggregate logs.jsonl --group-by department --sum total_cost
```

### 4. Inspect
Get full (redacted) details of a specific request:
```bash
./logq inspect logs.jsonl --id req_123
```

### 5. Tail
Watch your gateway traffic in real-time:
```bash
./logq tail logs.jsonl
```
