Prompt is required. Provide it via --prompt "<text>" or positional [prompt].
Oracle CLI v1.3.0 — GPT-5 Pro/GPT-5.1 for tough questions with code/file context.

Usage: oracle [options] [command] [prompt]

One-shot GPT-5 Pro / GPT-5.1 tool for hard questions that benefit from large
file context and server-side search.

Arguments:
  prompt                         Prompt text (shorthand for --prompt).

Options:
  -V, --version                  output the version number
  -p, --prompt <text>            User prompt to send to the model.
  -f, --file <paths...>          Files/directories or glob patterns to attach
                                 (prefix with !pattern to exclude). Files larger
                                 than 1 MB are rejected automatically. (default:
                                 [])
  -s, --slug <words>             Custom session slug (3-5 words).
  -m, --model <model>            Model to target (gpt-5-pro | gpt-5.1, or
                                 ChatGPT labels like "5.1 Instant" for browser
                                 runs). (default: "gpt-5-pro")
  -e, --engine <mode>            Execution engine (api | browser). If omitted,
                                 oracle picks api when OPENAI_API_KEY is set,
                                 otherwise browser. (choices: "api", "browser")
  --files-report                 Show token usage per attached file (also prints
                                 automatically when files exceed the token
                                 budget). (default: false)
  -v, --verbose                  Enable verbose logging for all operations.
                                 (default: false)
  --[no-]notify                  Desktop notification when a session finishes
                                 (default on unless CI/SSH).
  --[no-]notify-sound            Play a notification sound on completion
                                 (default off).
  --timeout <seconds|auto>       Overall timeout before aborting the API call
                                 (auto = 20m for gpt-5-pro, 30s otherwise).
                                 (default: "auto")
  --dry-run [mode]               Preview without calling the model (summary |
                                 json | full). (choices: "summary", "json",
                                 "full", default: false, preset: "summary")
  --render-markdown              Emit the assembled markdown bundle for prompt +
                                 files and exit. (default: false)
  --verbose-render               Show render/TTY diagnostics when replaying
                                 sessions. (default: false)
  --base-url <url>               Override the OpenAI-compatible base URL for API
                                 runs (e.g. LiteLLM proxy endpoint).
  --azure-endpoint <url>         Azure OpenAI Endpoint (e.g.
                                 https://resource.openai.azure.com/).
  --azure-deployment <name>      Azure OpenAI Deployment Name.
  --azure-api-version <version>  Azure OpenAI API Version.
  --browser-inline-files         Paste files directly into the ChatGPT composer
                                 instead of uploading attachments. (default:
                                 false)
  --browser-bundle-files         Bundle all attachments into a single archive
                                 before uploading. (default: false)
  --debug-help                   Show the advanced/debug option set and exit.
                                 (default: false)
  --heartbeat <seconds>          Emit periodic in-progress updates (0 to
                                 disable). (default: 30)
  --wait
  -h, --help                     display help for command

Commands:
  session [options] [id]         Attach to a stored session or list recent
                                 sessions when no ID is provided.
  status [options] [id]          List recent sessions (24h window by default) or
                                 attach to a session when an ID is provided.

Tips
• Oracle cannot see your project unless you pass --file … — attach the files/dirs you want it to read.
• Attach lots of source (whole directories beat single files) and keep total input under ~196k tokens.
• Oracle starts empty—open with a short project briefing (stack, services, build steps), spell out the question and prior attempts, and why it matters; the more explanation and context you provide, the better the response will be.
• Best results: 6–30 sentences plus key source files; very short prompts often yield generic answers.
• Oracle is one-shot: it does not remember prior runs, so start fresh each time with full context.
• Run --files-report to inspect token spend before hitting the API.
• Non-preview runs spawn detached sessions (especially gpt-5-pro API). If the CLI times out, do not re-run — reattach with oracle session <slug> to resume/inspect the existing run.
• Set a memorable 3–5 word slug via --slug "<words>" to keep session IDs tidy.
• Finished sessions auto-hide preamble logs when reattached; raw timestamps remain in the saved log file.
• Need hidden flags? Run oracle --help --verbose to list search/token/browser overrides.

Examples
  oracle --prompt "Summarize risks" --file docs/risk.md --files-report --preview
    Inspect tokens + files without calling the API.

  oracle --prompt "Explain bug" --file src/,docs/crash.log --files-report
    Attach src/ plus docs/crash.log, launch a background session, and capture the Session ID.

  oracle status --hours 72 --limit 50
    Show sessions from the last 72h (capped at 50 entries).

  oracle session <sessionId>
    Attach to a running/completed session and stream the saved transcript.

  oracle --prompt "Ship review" --slug "release-readiness-audit"
    Encourage the model to hand you a 3–5 word slug and pass it along with --slug.


Examples:
  # Quick API run with two files
  oracle --prompt "Summarize the risk register" --file docs/risk-register.md docs/risk-matrix.md

  # Browser run (no API key) + globbed TypeScript sources, excluding tests
  oracle --engine browser --prompt "Review the TS data layer" \
    --file "src/**/*.ts" --file "!src/**/*.test.ts"

