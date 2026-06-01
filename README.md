# Capstone Project: Telecom AI Operations Center

This repository contains the Telecom AI Operations Center application, built using LangGraph, CrewAI, LlamaIndex, and ADK (Agentic Development Kit).

## Prerequisites

1. **Python 3.10+** is required.
2. Ensure you have your API keys ready (Google Gemini, OpenAI, Tavily, etc.).

## Setup Instructions

1. **Install Dependencies**
   Run the following command to install all the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**
   Create a `.env` file in the root directory and populate it with your necessary API keys (Make sure never to commit your `.env` file!):
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   OPENWEATHERMAP_API_KEY=your_openweathermap_key_here
   ```

## How to Run the Application

The easiest way to start the application and all its microservices is by using the provided `run_all.py` script.

From the root of the project, run:
```bash
python run_all.py
```

This script will automatically start:
- **Network Diagnostics ADK Service** on `http://localhost:8001`
- **Billing Resolution ADK Service** on `http://localhost:8002`
- **Streamlit UI** on `http://localhost:8501`

Wait for all services to start up, and then open your browser and navigate to **[http://localhost:8501](http://localhost:8501)** to interact with the application.

## Stopping the Application

To shut down the UI and all background ADK services gracefully, simply press `Ctrl + C` in the terminal where `run_all.py` is running.
