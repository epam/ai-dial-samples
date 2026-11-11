# Preserve credentials and unrelated settings while migrating sample URLs.
def migrate_url: if type == "string" then
    sub("^http://adapter-dial-openai:5000(?=/|$)"; "http://model-provider:5000/compat/openai")
    | sub("^http://adapter-dial-bedrock:5000(?=/|$)"; "http://model-provider:5000/compat/bedrock")
    | sub("^http://adapter-dial-vertexai:5000(?=/|$)"; "http://model-provider:5000/compat/vertexai")
else . end;

walk(if type == "object" then
    with_entries(if (.key | test("(?i)(endpoint|base_?url)$")) then .value |= migrate_url else . end)
else . end)
# The sample advertises Responses; give Core its corresponding Ollama upstream.
| if .interfaces.openaiResponses.mode == "passthrough" and (.upstreams | type == "array") then
    .upstreams |= map(if .interfaces.openaiChatCompletions.endpoint == "http://ollama:11434/v1/chat/completions" then
        .interfaces.openaiResponses //= {"endpoint": "http://ollama:11434/v1/responses"}
    else . end)
else . end
