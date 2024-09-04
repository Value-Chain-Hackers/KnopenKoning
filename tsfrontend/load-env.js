const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// Path to the .env file one level up
const envPath = path.resolve(__dirname, '..', '.env');

if (fs.existsSync(envPath)) {
  // Load the .env file
  const envConfig = dotenv.parse(fs.readFileSync(envPath));
  
  // Set each environment variable
  for (const k in envConfig) {
    process.env[k] = envConfig[k];
    console.log(`Set environment variable: ${k}`);
  }

  console.log('.env file loaded successfully');
} else {
  console.log('.env file not found in parent directory');
}

// Log all environment variables
console.log('All environment variables:');
console.log(process.env);