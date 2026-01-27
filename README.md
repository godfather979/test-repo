
# 📈 Dhando: AI-Powered Stock Analysis

Mumbai Hack is an advanced financial analytics platform designed to empower investors with AI-driven insights for the Indian stock market. The system combines deterministic financial modeling with generative AI to provide real-time chart pattern recognition, sentiment analysis, and automated research.

## 🚀 Features

* **AI Chart Pattern Recognition**: Leverages Vision models to detect technical patterns (like Double Bottoms or Head and Shoulders) directly from TradingView chart screenshots.
* **Agentic Market Research**: Uses specialized AI agents and DuckDuckGo search to provide bullish or bearish signals based on current news and financial health.
* **Automated BSE News Summarization**: Fetches the latest corporate announcements from the Bombay Stock Exchange and provides concise summaries.
* **Financial Ratio Analysis**: Automatically calculates key metrics such as Debt/Equity, EBITDA Margin, and Interest Coverage using Yahoo Finance data.
* **Smart Watchlist & Caching**: Users can track stocks in a personalized wishlist, which triggers background workers to pre-compute and cache analysis for instant dashboard access.
* **Dynamic Themed UI**: A modern, responsive dashboard built with Next.js that features interactive charts and real-time data visualization.

## 🛠️ Tech Stack

### Frontend

* **Framework**: [Next.js 16](https://nextjs.org/) (App Router)
* **State Management**: [Zustand](https://github.com/pmndrs/zustand)
* **Styling**: [Tailwind CSS 4](https://tailwindcss.com/) & [Shadcn/UI](https://ui.shadcn.com/)
* **Animations**: [Framer Motion](https://www.framer.com/motion/)
* **Charts**: [Recharts](https://recharts.org/)

### Backend

* **Language**: [Python 3.11+](https://www.python.org/)
* **Framework**: [Flask](https://flask.palletsprojects.com/)
* **AI Framework**: [Agno AI](https://www.agno.com/) (Agentic workflows)
* **Database**: [Firebase Firestore](https://firebase.google.com/docs/firestore)
* **Auth**: [Firebase Authentication](https://firebase.google.com/docs/auth)

## 📂 Project Structure

```text
├── backend/
│   ├── main.py              # Flask API entry point and routes
│   ├── functions/           # Core logic for news, ratios, and AI agents
│   ├── charts/              # Local storage for generated chart images
│   └── .env                 # Backend environment variables
└── client/
    ├── app/                 # Next.js App Router and components
    ├── store/               # Zustand global state management
    ├── public/              # Static assets and master stock data
    └── package.json         # Frontend dependencies

```

## ⚙️ Installation & Setup

### Backend Setup

1. Navigate to the `backend` directory.
2. Install the required Python packages:
```bash
pip install flask flask-cors firebase-admin python-dotenv requests yfinance agno

```


3. Create a `.env` file with the following keys:
* `WEB_API_KEY`: Your Firebase Web API Key.
* `FIREBASE_CREDENTIALS`: Path to your service account JSON file.
* `GROQ_API_KEY`: For vision-based pattern recognition.


4. Run the server:
```bash
python main.py

```



### Frontend Setup

1. Navigate to the `client` directory.
2. Install dependencies:
```bash
npm install

```


3. Start the development server:
```bash
npm run dev

```


4. Access the application at `http://localhost:3000`.

## 📡 API Overview

| Endpoint | Method | Description |
| --- | --- | --- |
| `/user/signup` | POST | Registers a new user and initializes Firestore data. |
| `/me/wishlist/add` | POST | Adds a stock to the user's wishlist and starts background analysis. |
| `/chart-patterns` | POST | Generates and analyzes technical charts using AI Vision. |
| `/prediction` | POST | Triggers the Agno agent for stock sentiment and risk analysis. |
| `/me/cache` | GET | Returns all pre-calculated analysis for the user's dashboard. |
