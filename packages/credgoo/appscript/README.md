# Credgoo AppScript Integration

## Installation

1. Create a new Google Apps Script project
2. Copy the contents of `code.gs` into the script editor
3. Deploy the script as a Web App with the following settings:
   - Execute as: Me
   - Who has access: Anyone with Google account

## Configuration

1. Set script properties (Script Properties > Project Properties):
   - `SECRET_TOKEN`: Your authentication token (must match credgoo CLI)
   - `ENCRYPTION_KEY`: Your encryption key (must match credgoo CLI)
2. Create a Google Sheet named "keys" with columns:
   - Column A: Service names
   - Column B: API keys

## Integration with Credgoo CLI

The AppScript template is designed to work seamlessly with the credgoo CLI:

```bash
credgoo SERVICE_NAME --token YOUR_SECRET_TOKEN --key YOUR_ENCRYPTION_KEY --url YOUR_APP_SCRIPT_URL
```

## Example Workflow

1. Add your API keys to the "keys" spreadsheet
2. Deploy the AppScript web app
3. Use credgoo CLI to retrieve encrypted keys
4. The CLI automatically decrypts keys using your encryption key

## Security Notes

- Never commit your `SECRET_TOKEN` or `ENCRYPTION_KEY` to version control
- Rotate tokens and keys periodically
- Restrict access to the Google Sheet containing API keys
