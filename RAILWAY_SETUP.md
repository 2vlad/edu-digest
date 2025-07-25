# Railway Deployment Setup Guide

## Problem Summary
The Telegram digest is not working in production because the Telegram reader fails to initialize. This is because bot tokens cannot read channels - you need a user session.

## Solution Steps

### 1. Create Telegram Session Locally
```bash
# First, ensure you have the session file locally
python create_session_for_railway.py
# or
python setup_telegram_session.py
```

This will create a `railway_session.session` file after you authenticate with your phone number.

### 2. Convert Session to Base64
```bash
python session_to_base64.py
```

This will:
- Read the `railway_session.session` file
- Convert it to base64
- Display the value you need to add to Railway
- Save it to `session_base64.txt` for convenience

### 3. Add to Railway Environment Variables
1. Go to your Railway project dashboard
2. Navigate to Settings → Variables
3. Add a new variable:
   - Name: `TELEGRAM_SESSION_BASE64`
   - Value: (paste the base64 string from step 2)
4. Deploy your changes

### 4. Verify the Fix
After deployment, check the logs. You should see:
- `🔐 Found TELEGRAM_SESSION_BASE64 in environment, decoding...`
- `✅ Session file decoded and saved`
- `🔑 Found existing session file, using it for user access`
- `✅ Telethon client authorized successfully`

## Important Notes

1. **Security**: The session file contains your Telegram authentication. Keep it secure and don't share it publicly.

2. **Session Expiry**: If the session expires, you'll need to:
   - Create a new session locally
   - Convert to base64 again
   - Update the Railway environment variable

3. **Alternative**: If you can't use a user session, you would need to:
   - Use a different method to get channel content (like RSS feeds)
   - Or manually add the bot to all channels as an admin (not practical for public channels)

## Troubleshooting

If it still doesn't work:
1. Check that all required environment variables are set in Railway:
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH` 
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_SESSION_BASE64`

2. Ensure the session was created with the same API_ID and API_HASH

3. Check Railway logs for specific error messages