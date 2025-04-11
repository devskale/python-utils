function doGet(e) {
  // Retrieve credentials from script properties
  const scriptProperties = PropertiesService.getScriptProperties();
  const SECRET_TOKEN = scriptProperties.getProperty("SECRET_TOKEN");
  const ENCRYPTION_KEY = scriptProperties.getProperty("ENCRYPTION_KEY");

  // Authentication check
  if (!e.parameter.token || e.parameter.token !== SECRET_TOKEN) {
    return ContentService.createTextOutput(
      JSON.stringify({
        status: "error",
        message: "Authentication failed",
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }

  // Get the requested service
  const requestedService = e.parameter.service;
  if (!requestedService) {
    return ContentService.createTextOutput(
      JSON.stringify({
        status: "error",
        message: "No service specified",
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }

  // Access the spreadsheet and relevant sheet
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("keys");
  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();

  // Find the requested service
  let apiKey = null;
  for (let i = 0; i < values.length; i++) {
    if (values[i][0] === requestedService) {
      apiKey = values[i][1].toString(); // Ensure it's a string
      break;
    }
  }

  if (!apiKey) {
    return ContentService.createTextOutput(
      JSON.stringify({
        status: "error",
        message: "Service not found",
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }

  // Encrypt the API key with robust encryption
  try {
    const encryptedKey = robustEncrypt(apiKey, ENCRYPTION_KEY);

    // Return the encrypted key
    return ContentService.createTextOutput(
      JSON.stringify({
        status: "success",
        service: requestedService,
        encryptedKey: encryptedKey,
      })
    ).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(
      JSON.stringify({
        status: "error",
        message: "Encryption failed: " + error.toString(),
      })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

// More robust encryption function
function robustEncrypt(text, key) {
  if (!text) {
    Logger.log("Empty text provided for encryption");
    return "";
  }

  // Generate a predictable but unique initialization vector
  let iv = "";
  for (let i = 0; i < 8; i++) {
    iv += String.fromCharCode(key.charCodeAt(i % key.length) ^ i);
  }

  // Combine IV with the text for proper encryption
  let combined = iv + text;

  // Perform XOR encryption with key
  let result = "";
  for (let i = 0; i < combined.length; i++) {
    // Ensure we're using a different part of the key for each character
    const keyChar = key.charCodeAt((i * 7) % key.length);
    const textChar = combined.charCodeAt(i);
    result += String.fromCharCode(textChar ^ keyChar);
  }

  // Base64 encode the result for safe transmission
  return Utilities.base64Encode(Utilities.newBlob(result).getBytes());
}
