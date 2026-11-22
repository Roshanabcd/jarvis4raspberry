# FreeLLMAPI for JARVIS chat

Run the gateway on the same host and network namespace as the JARVIS backend. JARVIS uses its OpenAI-compatible endpoint at http://127.0.0.1:3001/v1/chat/completions. The /agents page is the gateway UI. The actual protocol and available models must be confirmed against your running gateway.

Set FREELLMAPI_API_KEY to a fresh unified key and FREELLMAPI_MODEL to an exact model ID served by the gateway. For a foreground server, enter these in its launch shell:

```bash
read -rs -p 'New gateway key: ' FREELLMAPI_API_KEY; echo
read -r -p 'Gateway model ID: ' FREELLMAPI_MODEL
export FREELLMAPI_API_KEY FREELLMAPI_MODEL
```

For a managed service supply those variables through its private environment and restart that instance. Open AI Chat and select the freellmapi model. Start with Conversation only. Listing the configured model does not verify gateway reachability. Claude CLI setup is separate from JARVIS provider registration.
