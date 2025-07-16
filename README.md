# 📈 TradingPoint - Market Data WebApp

<img width="1147" height="778" alt="Screenshot from 2025-07-16 14-18-26" src="https://github.com/user-attachments/assets/73808c02-402d-410e-ae82-0d1ebea5f091" />


> A Django-powered dashboard for tracking stocks, ETFs, and cryptocurrencies with near-real-time data visualization.

##  Key Features

- ⏱ **15-second delayed market data** (HTTPS polling)
- 🛡 **Automatic fallback** to realistic dummy data
- 📊 **Interactive charts** with 6 timeframes
- 🔍 Asset search and filtering
- 📱 Fully responsive design

## 🛠 Technology Stack

- **Backend**: Python, Django 4.0+ Framework, PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript
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


## API Notes
  Free-tier API keys have rate limits
  Dummy data activates when:
   API quota exceeded

   Network issues

   Invalid symbols requested

## Contributing
  I welcome all contributions! Here's how:
  
  Fork the repository
  
  Create your feature branch (git checkout -b feature/amazing-feature)
  
  Commit your changes (git commit -m 'Add some amazing feature')
  
  Push to the branch (git push origin feature/amazing-feature)
  
  Open a Pull Request
