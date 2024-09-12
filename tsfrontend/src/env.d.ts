declare namespace NodeJS {
    interface ProcessEnv {
      REACT_APP_API_URL: string;
      REACT_APP_API_KEY: string;
      OLLAMA_HOST: string;
      REACT_APP_OLLAMA_HOST: string;
      REACT_APP_BACKEND_URL: string;
      // Add other environment variables here
      [key: string]: string | undefined;
    }
  }