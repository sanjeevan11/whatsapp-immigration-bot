# WhatsApp Immigration Bot

A Flask-based WhatsApp bot for UK immigration services with automated case management, Google Apps Script integration, and AI-powered responses.

## Features

- **Multi-Service Support**: Handles Family Immigration, Work Immigration, Study Immigration, Visit Immigration, Settlement, Citizenship, Asylum, and Specialist Visas
- **Interactive Eligibility Assessment**: Guides users through visa-specific questions
- **Smart Document Checklist**: Generates personalized checklists based on user answers
- **Media Upload**: Supports document uploads (images, PDFs, audio, video) with Google Drive integration
- **AI-Powered Q&A**: Uses OpenRouter API for complex immigration queries
- **Case Management**: Integrates with Google Apps Script for case registration, Google Sheets tracking, and Drive folder organization
- **Automated Email Notifications**: Sends intake summaries to admin
- **FAQ System**: Built-in FAQs for common visa questions
- **Booking Integration**: Calendar.ly and Google Calendar integration
- **Red Flag Detection**: Identifies potential issues (refusals, overstays, criminal records)
- **Duplicate Check**: Prevents duplicate case entries

## Tech Stack

- **Backend**: Python 3.x with Flask
- **WhatsApp API**: Meta WhatsApp Business Platform
- **AI**: OpenRouter API (Qwen model)
- **Storage**: Google Drive via Apps Script
- **Database**: Google Sheets for case tracking
- **Deployment**: Cyclic.sh (or any Flask-compatible platform)

## Prerequisites

1. **WhatsApp Business Account**
   - Meta Business account
   - WhatsApp Business API access
   - Phone number ID and Access Token

2. **Google Apps Script**
   - Deployed Apps Script web app
   - Drive folder for document storage
   - Google Sheet for case tracking

3. **OpenRouter Account**
   - API key for AI responses

## Environment Variables

Create a `.env` file with the following:

```bash
# WhatsApp Configuration
WA_ACCESS_TOKEN=your_whatsapp_access_token
WA_PHONE_ID=your_phone_number_id
WA_VERIFY_TOKEN=your_verify_token
API_VER=v18.0

# Google Apps Script
APPSCRIPT_URL=your_apps_script_deployment_url

# OpenRouter AI
OPENROUTER_KEY=your_openrouter_api_key
OPENROUTER_MODEL=qwen/qwen3-30b-a3b:free

# Admin Settings
ADMIN_EMAIL=your_admin_email

# Google Drive & Sheets
DRIVE_FOLDER_ID=your_drive_folder_id
SHEET_ID=your_google_sheet_id
SHEET_TAB=Cases

# Calendar (optional)
CALENDLY_URL=your_calendly_link
CAL_TZ=Europe/London

# Limits
MAX_MEDIA_BYTES=12582912  # 12MB

# Deployment
PORT=8080
```

## Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/sanjeevan11/whatsapp-immigration-bot.git
   cd whatsapp-immigration-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file with your credentials (see `.env.example`)

4. Run the application:
   ```bash
   python main.py
   ```

5. For local testing with WhatsApp webhooks, use ngrok:
   ```bash
   ngrok http 5000
   ```

### Deploy to Cyclic.sh (Free)

1. Fork/clone this repository to your GitHub account

2. Go to [Cyclic.sh](https://cyclic.sh) and sign in with GitHub

3. Click "Connect a new app" and select this repository

4. Configure environment variables in Cyclic dashboard (all variables from `.env.example`)

5. Cyclic will auto-deploy. Your webhook URL will be:
   ```
   https://your-app-name.cyclic.app/webhook
   ```

6. Configure this webhook URL in Meta Business Suite:
   - Go to WhatsApp > Configuration > Webhook
   - Enter callback URL: `https://your-app-name.cyclic.app/webhook`
   - Enter verify token (same as `WA_VERIFY_TOKEN`)
   - Subscribe to `messages` field

## WhatsApp Business Setup

1. **Create Meta Business Account**: [business.facebook.com](https://business.facebook.com)
2. **Set up WhatsApp Business API**: [developers.facebook.com/docs/whatsapp](https://developers.facebook.com/docs/whatsapp)
3. **Get Access Token**: From App Dashboard > WhatsApp > API Setup
4. **Get Phone Number ID**: From WhatsApp > API Setup
5. **Configure Webhook**: 
   - Callback URL: `https://your-domain.com/webhook`
   - Verify Token: Match `WA_VERIFY_TOKEN`
   - Subscribe to: `messages`

## Google Apps Script Setup

The bot requires a Google Apps Script web app for:
- Case registration in Google Sheets
- Document uploads to Google Drive
- Email notifications
- URL shortening (optional)

**Apps Script should expose these actions:**
- `register`: Create case entry
- `appendrow`: Add to Sheet
- `uploadmedia`: Save file to Drive
- `shortenurl`: Shorten links (optional)
- `sendemail`: Send notifications
- `fuzzyduplicate`: Check duplicates

Deploy as Web App:
- Execute as: Me
- Who has access: Anyone

## Usage Flow

1. **User sends message** → Bot presents service categories
2. **User selects category** (e.g., Family Immigration) → Sub-services shown
3. **User selects sub-service** (e.g., Spouse Visa) → Eligibility questions begin
4. **User answers questions** → Bot tracks responses
5. **Upload documents** → Saved to Google Drive
6. **Case registration** → Stored in Google Sheets
7. **Document checklist** → Smart, personalized list
8. **FAQ access** → Browse common questions
9. **AI Q&A** → Ask complex questions
10. **Booking CTA** → Calendly/Google Calendar links

## API Endpoints

### `GET /webhook`
Webhook verification for WhatsApp

**Query Params:**
- `hub.mode`: subscribe
- `hub.verify_token`: Your verify token
- `hub.challenge`: Challenge string

**Returns:** Challenge string if token matches

### `POST /webhook`
Receives WhatsApp messages

**Body:** WhatsApp webhook payload

**Returns:** `{"status": "ok"}`

### `GET /`
Health check

**Returns:** "OK"

## Project Structure

```
whatsapp-immigration-bot/
├── main.py              # Main Flask application
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## Keep-Alive (Free Hosting)

If using free hosting that sleeps after inactivity:

1. Sign up for [UptimeRobot](https://uptimerobot.com) (free)
2. Create HTTP(s) monitor
3. Set URL: `https://your-app.cyclic.app/`
4. Interval: 5 minutes
5. This pings your app every 5 minutes to keep it awake

## Updating the Bot

### On Cyclic.sh
1. Push changes to GitHub:
   ```bash
   git add .
   git commit -m "Your update message"
   git push origin main
   ```
2. Cyclic auto-deploys from GitHub (takes 1-2 minutes)

### Environment Variables
Update in Cyclic dashboard under Variables tab (requires redeploy)

## Troubleshooting

### Webhook Verification Fails
- Ensure `WA_VERIFY_TOKEN` matches Meta webhook config
- Check webhook URL is publicly accessible
- Verify HTTPS (required by Meta)

### Messages Not Sending
- Verify `WA_ACCESS_TOKEN` is valid and not expired
- Check `WA_PHONE_ID` is correct
- Ensure phone number is registered in WhatsApp Business
- Check WhatsApp API rate limits

### Apps Script Errors
- Verify `APPSCRIPT_URL` is the web app URL (ends with `/exec`)
- Ensure Apps Script is deployed as "Anyone" access
- Check Apps Script logs for errors

### File Upload Issues
- Verify `DRIVE_FOLDER_ID` is correct
- Ensure Apps Script has Drive permissions
- Check file size under `MAX_MEDIA_BYTES` (12MB default)

### AI Responses Not Working
- Verify `OPENROUTER_KEY` is valid
- Check OpenRouter account has credits/free tier
- Ensure `OPENROUTER_MODEL` exists

## Security Notes

- **Never commit `.env` file** - Use `.env.example` template only
- **Rotate tokens regularly** - Especially WhatsApp access tokens
- **Validate webhook signatures** - Implement Meta signature validation (optional but recommended)
- **Rate limiting** - Implement rate limiting for production
- **Input validation** - Bot validates user inputs
- **No sensitive data in logs** - Avoid logging tokens/passwords

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

MIT License - feel free to use for personal or commercial projects

## Support

For issues or questions:
- Open a GitHub issue
- Email: your_support_email@example.com

## Roadmap

- [ ] Webhook signature verification
- [ ] Rate limiting
- [ ] Multi-language support
- [ ] Voice message transcription
- [ ] Advanced analytics dashboard
- [ ] Template message support
- [ ] Payment integration
- [ ] Video consultation booking

## Credits

Built with:
- [Flask](https://flask.palletsprojects.com/)
- [WhatsApp Business Platform](https://developers.facebook.com/docs/whatsapp)
- [OpenRouter](https://openrouter.ai/)
- [Google Apps Script](https://developers.google.com/apps-script)

---

**Made with ❤️ for UK Immigration Services**
