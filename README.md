# 📈 TradingPoint - Market Data WebApp

![Market Screenshot]()
<img width="1206" height="786" alt="market" src="https://github.com/user-attachments/assets/7fa5a3f7-a659-45d0-b5ae-52b0f018dca9" />

> A Django-powered dashboard for tracking stocks, ETFs, and cryptocurrencies with near-real-time data visualization.

## ✨ Key Features

- ⏱ **15-second delayed market data** (HTTPS polling)
- 🛡 **Automatic fallback** to realistic dummy data
- 📊 **Interactive charts** with 6 timeframes
- 🔍 Asset search and filtering
- 📱 Fully responsive design

## 🛠 Technology Stack

- **Backend**: Python, Django 4.0+ Framework, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (Chart.js)
- **APIs**: Twelve Data (stocks), CoinGecko (crypto)
- **Caching**: 5-minute API response caching

## 🚀 Quick Setup

# 1. Clone repository
git clone https://github.com/yourusername/tradingpoint.git
cd tradingpoint

# 2. Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
echo "TWELVE_DATA_API_KEY=your_key_here" > .env
echo "SECRET_KEY=your_secret_key" >> .env
echo "DEBUG=True" >> .env

# 5. Run migrations
python manage.py migrate

# 6. Start development server
python manage.py runserver

Visit http://localhost:8000 in your browser.

🔄 How It Works
  Data Flow Diagram
  Diagram
  Code

sequenceDiagram
    Client->>+Django: GET /get_live_data (every 15s)
    Django->>+TwelveData: API Request
    TwelveData-->>-Django: Market Data
    Django-->>-Client: JSON Response
    Client->>Chart.js: Update Visualization

## API Notes
  Free-tier API keys have rate limits
  Dummy data activates when:
  🔥 API quota exceeded
  🌐 Network issues
  ❌ Invalid symbols requested

## Contributing
  I welcome all contributions! Here's how:
  
  Fork the repository
  
  Create your feature branch (git checkout -b feature/amazing-feature)
  
  Commit your changes (git commit -m 'Add some amazing feature')
  
  Push to the branch (git push origin feature/amazing-feature)
  
  Open a Pull Request
