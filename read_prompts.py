import json

with open(r'C:\Users\stali\.gemini\antigravity\brain\3efcf8e4-af9f-4641-965b-9ebc53027d75\.system_generated\logs\transcript.jsonl', encoding='utf-8') as f:
    for line in f:
        if 'invoke_subagent' in line:
            data = json.loads(line)
            try:
                for tc in data.get('tool_calls', []):
                    args = tc.get('arguments', {})
                    for sa in args.get('Subagents', []):
                        print(f"--- ROLE: {sa.get('Role')} ---")
                        print(sa.get('Prompt'))
            except Exception as e:
                pass
