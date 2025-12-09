# Secure Process: Add Gemini API Key to Production

## ⚠️ IMPORTANT SECURITY NOTES

1. **NEVER commit API keys to git**
2. The `.env` file is already in `.gitignore` - this is correct
3. We'll add the key directly on the server via SSH
4. The key will NEVER touch your local machine or git history

## Step 1: Get Your Gemini API Key

If you don't have one yet:
1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key
3. Copy it to your clipboard

## Step 2: Add Key to Production Server (SECURE METHOD)

Run this command on your LOCAL machine. It will prompt you for the API key and add it securely:

```bash
# This creates a secure SSH session that adds the key without saving it locally
ssh deploy@178.156.161.140 "read -s -p 'Enter Gemini API Key: ' GEMINI_KEY && echo '' && echo 'GEMINI_API_KEY='\$GEMINI_KEY >> /opt/citations/.env && echo '✓ Key added to .env'"
```

**What this does:**
- Opens SSH connection to production server
- Prompts YOU to type the API key (input is hidden with `-s`)
- Appends it to `/opt/citations/.env` on the server
- Key never touches your local filesystem or git

## Step 3: Verify Key Was Added (WITHOUT revealing it)

```bash
ssh deploy@178.156.161.140 "grep -c 'GEMINI_API_KEY' /opt/citations/.env"
```

Should output: `1`

## Step 4: Restart Backend Service

```bash
ssh deploy@178.156.161.140 "sudo systemctl restart citation-backend"
```

## Step 5: Verify Gemini Provider Initializes

```bash
ssh deploy@178.156.161.140 "tail -20 /opt/citations/logs/app.log | grep -i gemini"
```

Should see: "Initialized GeminiProvider" (or similar success message)
Should NOT see: "Failed to initialize GeminiProvider"

## Alternative: Manual Method (If you prefer)

1. SSH into server: `ssh deploy@178.156.161.140`
2. Edit the file: `nano /opt/citations/.env`
3. Add line: `GEMINI_API_KEY=your-key-here`
4. Save (Ctrl+X, Y, Enter)
5. Restart: `sudo systemctl restart citation-backend`
6. Exit SSH: `exit`

## Verification After Restart

Test with a real request that includes `X-Model-Preference: model_b` header.
Check logs for:
- ✅ "Initialized GeminiProvider"
- ✅ "PROVIDER_SELECTION: ... model=model_b status=success fallback=False"

## Security Checklist

- [ ] API key added to server's `/opt/citations/.env`
- [ ] `.env` is in `.gitignore` (already confirmed ✓)
- [ ] Backend service restarted
- [ ] Gemini provider initializes successfully
- [ ] Test request shows model_b without fallback
- [ ] Dashboard shows "Gemini-2.5-Flash" for model_b requests

## Troubleshooting

**If Gemini still fails:**
```bash
# Check if key is present (without revealing it)
ssh deploy@178.156.161.140 "grep GEMINI_API_KEY /opt/citations/.env | cut -d= -f1"

# Check logs for initialization
ssh deploy@178.156.161.140 "grep 'GeminiProvider' /opt/citations/logs/app.log | tail -5"

# Restart service again
ssh deploy@178.156.161.140 "sudo systemctl restart citation-backend"
```
