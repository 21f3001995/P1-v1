Project Dir Structure

P1-v1/
├─ app.py                 # Main FastAPI API endpoint
├─ github_utils.py        # Functions to create repo, push, enable Pages
├─ llm_generator.py       # Functions to generate app code from brief
├─ attachment_utils.py    # Handle attachments from POST
├─ config.py              # Your GitHub token, secret, username
├─ attachments/           # Temp folder to store uploaded attachments
└─ README.md

# $env:PATH += ";C:\Program Files (x86)\GitHub CLI"