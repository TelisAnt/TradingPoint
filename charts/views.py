from django.conf import settings
from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
import psycopg2
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.hashers import make_password  # For password hashing
from datetime import datetime  # For timestamping
import re
from django.core.exceptions import ValidationError #injections
from django.db import transaction   # For transaction management
from django.db import connection, transaction # For database operations
from django.views.decorators.csrf import csrf_protect
import logging
import requests
from .models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page # Cache the live data endpoint to reduce API calls and improve performance



class homepage(View):
    def get(self, request):
        # Check if user is logged in by checking the session
        if 'user_id' in request.session:
            context = {
                'username': request.session['username'],
                'is_authenticated': True
            }
        else:
            context = {
                'is_authenticated': False
            }
        return render(request, 'charts/homepage.html', context)

logger = logging.getLogger(__name__)
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(ratelimit(key='post:username', rate='5/m', method='POST'), name='dispatch')
class login_view(View):
    def get(self, request):
        context = {
            'title': 'Login',
            'login_message': 'Please enter your credentials to log in'
        }
        return render(request, 'charts/login.html', context)

    def validate_inputs(self, username, password):
        if not username or not password:
            raise ValidationError('Both username and password are required')
        if len(username) > 50:
            raise ValidationError('Username too long')
        if len(password) > 128:
            raise ValidationError('Password too long')

    @method_decorator(ratelimit(key='post:username', rate='5/m', method='POST'))
    def post(self, request):
        try:
            # Get and sanitize inputs
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')

            # Input validation
            self.validate_inputs(username, password)

            # Use Django's connection instead of raw psycopg2
            with connection.cursor() as cursor:
                # Parameterized query to prevent SQL injection
                cursor.execute(
                    "SELECT id, username, password, is_admin FROM USERS WHERE username = %s AND is_active = TRUE LIMIT 1",
                    [username]
                )
                user = cursor.fetchone()

                if not user:
                    # Log failed login attempt (username not found)
                    logger.warning(f"Failed login attempt - username not found: {username}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid credentials'  # Generic message to avoid enumeration
                    }, status=401)

                user_id, db_username, hashed_password, is_admin = user

                # Secure password verification
                if not check_password(password, hashed_password):
                    # Log failed login attempt (wrong password)
                    logger.warning(f"Failed login attempt - wrong password for user: {username}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid credentials'
                    }, status=401)

                # Successful login
                request.session.cycle_key()
                request.session['user_id'] = user_id
                request.session['username'] = db_username
                request.session['is_admin'] = is_admin
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
                
                # Return redirect URL
                next_url = request.POST.get('next', settings.LOGIN_REDIRECT_URL)
                return JsonResponse({
                    'success': True,
                    'redirect': next_url
                })
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except psycopg2.Error as e:
            logger.error(f"Database error during login: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'System error. Please try again later.'
            }, status=500)
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred.'
            }, status=500)

class logout_view(View):
    def get(self, request):
        logout(request)  # This logs the user out
        return redirect('login')  # Redirect to login page with a message
    
    def post(self, request):
        logout(request)
        return redirect('login')

class register_view(View):
    def validate_username(self, username):  #Validate username format
        if len(username) < 4:
            raise ValidationError('Username must be at least 4 characters long.')
        if not re.match(r'^[\w.@+-]+\Z', username):
            raise ValidationError('Username can only contain letters, numbers, and @/./+/-/_ characters.')

    def validate_email(self, email): #Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError('Please enter a valid email address.')

    def validate_password(self, password):# Validate password
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long.')
        if not any(char.isdigit() for char in password):
            raise ValidationError('Password must contain at least one digit.')
        if not any(char.isupper() for char in password):
            raise ValidationError('Password must contain at least one uppercase letter.')

    def validate_age(self, age): # Age
        if age < 18:
            raise ValidationError('You must be at least 18 years old to register.')

    def check_existing_user(self, cursor, username, email): #Existing user check
        cursor.execute(
            "SELECT 1 FROM USERS WHERE username = %s OR email = %s LIMIT 1",
            [username, email]
        )
        return cursor.fetchone() is not None
    
    @transaction.atomic
    def post(self, request):
        try:
            # Get and sanitize form data
            firstname = request.POST.get('firstname', '').strip()
            lastname = request.POST.get('lastname', '').strip()
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip().lower()
            age = int(request.POST.get('age', 0))
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirmPassword', '')

            # Validate all required fields are present
            if not all([firstname, lastname, username, email, password, confirm_password]):
                raise ValidationError('All fields are required.')

            # Validate password match
            if password != confirm_password:
                raise ValidationError('Passwords do not match.')

            # Run all validations
            self.validate_username(username)
            self.validate_email(email)
            self.validate_password(password)
            self.validate_age(age)

            # Check for existing user using Django's ORM
            if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                raise ValidationError('Username or email already exists.')

            # Create user using Django's User model
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                firstname=firstname,
                lastname=lastname,
                age=age,
                is_admin=False
            )

            # Log the user in
            login(request, user)

            return JsonResponse({
                'success': True,
                'redirect': '/charts/profile/'
            })

        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred. Please try again.'
            }, status=500)


    def get(self, request):
        context = {
            'title': 'Register',
            'register_message': 'Create a new account to get started'
        }
        return render(request, 'charts/register.html', context)

    @transaction.atomic
    def post(self, request):
        try:
            # Get and sanitize form data
            firstname = request.POST.get('firstname', '').strip()
            lastname = request.POST.get('lastname', '').strip()
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip().lower()
            age = int(request.POST.get('age', 0))
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirmPassword', '')

            # Validate all required fields are present
            if not all([firstname, lastname, username, email, password, confirm_password]):
                raise ValidationError('All fields are required.')

            # Validate password match
            if password != confirm_password:
                raise ValidationError('Passwords do not match.')

            # Run all validations
            self.validate_username(username)
            self.validate_email(email)
            self.validate_password(password)
            self.validate_age(age)

            # Database operations
            with connection.cursor() as cursor:
                # Check for existing user
                if self.check_existing_user(cursor, username, email):
                    raise ValidationError('Username or email already exists.')

                # Hash password securely
                hashed_password = make_password(password)

                # Insert new user with parameterized query
                cursor.execute("""
                    INSERT INTO USERS 
                    (firstname, lastname, username, password, email, age, is_admin, is_active, last_login)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, [
                    firstname,
                    lastname,
                    username,
                    hashed_password,
                    email,
                    age,
                    False,  # is_admin
                    True,   # is_active
                    datetime.now()
                ])
                user_id = cursor.fetchone()[0]

            request.session['user_id'] = user_id
            request.session['username'] = username
            request.session['is_admin'] = False
            request.session.cycle_key()  # Security measure

            return JsonResponse({
                'success': True,
                'redirect': '/charts/profile/'
            })

        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except psycopg2.Error as e:
            print(f"Database error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Registration failed due to database error.'
            }, status=500)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred. Please try again.'
            }, status=500)

class profile_view(View):
    def get(self, request): 
        if 'user_id' not in request.session:
            return redirect(settings.LOGIN_URL)  # Redirect to login if not authenticated
        
        user_id = request.session['user_id']
        
        try:
            # Connect to Database
            conn = psycopg2.connect(
                dbname='TradingUsersdb',
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            cursor = conn.cursor()
            
            # Fetch user profile
            cursor.execute("""
                SELECT 
                    id,
                    firstname, 
                    lastname, 
                    username, 
                    email, 
                    age
                FROM USERS 
                WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
            
            if user:
                context = {
                    'title': 'Profile',
                    'user': {
                        'id': user[0],
                        'firstname': user[1],
                        'lastname': user[2],
                        'username': user[3],
                        'email': user[4],
                        'age': user[5]
                    }
                }
                return render(request, 'charts/profile.html', context)
            else:
                return redirect('login')
                
        except Exception as e:
            print("Database error:", e)
            return redirect('login')
        finally:
            if 'conn' in locals():
                conn.close()

class markets(View):
    def get(self,request):
        context = {
            'title': 'Markets Overview',
            'markets': [
                {'name': 'Stock Market', 'description': 'Latest stock market trends'},
                {'name': 'Forex Market', 'description': 'Current forex rates and trends'},
                {'name': 'Crypto Market', 'description': 'Latest cryptocurrency news'},
            ],
            'market_message': 'Stay updated with the latest market trends'
        }
        return render(request, 'charts/markets.html', context) 


@cache_page(60 * 5)
def get_live_data(request):
    symbol = request.GET.get('symbol')
    asset_type = request.GET.get('type', '').upper()
    
    if not symbol:
        return JsonResponse({'error': 'Missing symbol parameter'}, status=400)
    
    try:
        if asset_type == 'CRYPTO':
            # CoinGecko for crypto (Twelve Data has limited crypto support)
            coin_id_map = {
                'BTC-USD': 'bitcoin',
                'ETH-USD': 'ethereum'
            }
            coin_id = coin_id_map.get(symbol)
            
            if not coin_id:
                return JsonResponse({'error': 'Unsupported cryptocurrency'}, status=400)
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if coin_id not in data:
                return JsonResponse({'error': 'Symbol not found'}, status=404)
            
            price = data[coin_id]['usd']
            change_percent = data[coin_id]['usd_24h_change']
            change = (price * change_percent) / 100
            
            return JsonResponse({
                'symbol': symbol,
                'price': price,
                'change': change,
                'changePercent': change_percent
            })
            
        else:  # For stocks/ETFs - Twelve Data
            params = {
                'symbol': symbol,
                'apikey': settings.TWELVE_DATA_API_KEY
            }
            response = requests.get(
                'https://api.twelvedata.com/quote',
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if 'status' in data and data['status'] == 'error':
                return JsonResponse({
                    'error': data.get('message', 'Error from Twelve Data API'),
                    'api_response': data
                }, status=502)
            
            try:
                price = float(data['close'])
                change = float(data['change'])
                change_percent = float(data['percent_change'])
                
                return JsonResponse({
                    'symbol': symbol,
                    'price': price,
                    'change': change,
                    'changePercent': change_percent
                })
            except (KeyError, ValueError) as e:
                return JsonResponse({
                    'error': 'Failed to parse Twelve Data response',
                    'details': str(e),
                    'api_response': data
                }, status=502)
                
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'error': 'External API request failed',
            'details': str(e)
        }, status=502)
    except Exception as e:
        return JsonResponse({
            'error': 'Internal server error',
            'details': str(e)
        }, status=500)

@cache_page(60 * 5)
def get_chart_data(request):
    symbol = request.GET.get('symbol')
    asset_type = request.GET.get('type', '').upper()
    timeframe = request.GET.get('timeframe', '1m')
    
    if not symbol:
        return JsonResponse({'error': 'Missing symbol parameter'}, status=400)
    
    try:
        if asset_type == 'CRYPTO':
            # CoinGecko for crypto
            timeframe_map = {
                '1d': 1,
                '1w': 7,
                '1m': 30,
                '3m': 90,
                '1y': 365,
                'all': 'max'
            }
            days = timeframe_map.get(timeframe, 30)
            
            coin_id_map = {
                'BTC-USD': 'bitcoin',
                'ETH-USD': 'ethereum'
            }
            coin_id = coin_id_map.get(symbol)
            
            if not coin_id:
                return JsonResponse({'error': 'Unsupported cryptocurrency'}, status=400)
            
            price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
            price_response = requests.get(price_url)
            price_data = price_response.json()
            
            chart_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}"
            chart_response = requests.get(chart_url)
            chart_data = chart_response.json()
            
            prices = [{
                'date': datetime.fromtimestamp(point[0]/1000).isoformat(),
                'price': point[1]
            } for point in chart_data['prices']]
            
            current_price = price_data[coin_id]['usd']
            change_percent = price_data[coin_id]['usd_24h_change']
            change = (current_price * change_percent) / 100
            
            return JsonResponse({
                'chartData': prices,
                'currentPrice': current_price,
                'change': change,
                'changePercent': change_percent,
                'open': None,
                'high': None,
                'low': None,
                'volume': None
            })

        else:  # For stocks/ETFs - Twelve Data
            # Map timeframe to Twelve Data parameters
            interval_map = {
                '1d': '1h',
                '1w': '1day',
                '1m': '1day',
                '3m': '1day',
                '1y': '1month',
                'all': '1month'
            }
            
            output_size_map = {
                '1d': 24,
                '1w': 7,
                '1m': 30,
                '3m': 90,
                '1y': 12,
                'all': 120  # Maximum for free tier
            }
            
            interval = interval_map.get(timeframe, '1day')
            output_size = output_size_map.get(timeframe, 30)
            
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': output_size,
                'apikey': settings.TWELVE_DATA_API_KEY
            }
            
            response = requests.get('https://api.twelvedata.com/time_series', params=params)
            data = response.json()
            
            if 'status' in data and data['status'] == 'error':
                return JsonResponse({'error': data.get('message', 'Error from Twelve Data API')}, status=502)
            
            if 'values' not in data:
                return JsonResponse({'error': 'No time series data found'}, status=502)
            
            # Process Twelve Data response
            time_series_array = [{
                'date': point['datetime'],
                'price': float(point['close']),
                'open': float(point['open']),
                'high': float(point['high']),
                'low': float(point['low']),
                'volume': int(float(point['volume']))
            } for point in data['values']]
            
            # Sort by date ascending
            time_series_array.sort(key=lambda x: x['date'])
            
            # Get the latest data point for current price
            latest_data = time_series_array[-1]
            previous_data = time_series_array[-2] if len(time_series_array) > 1 else latest_data
            
            change = latest_data['price'] - previous_data['price']
            change_percent = (change / previous_data['price']) * 100
            
            return JsonResponse({
                'chartData': time_series_array,
                'currentPrice': latest_data['price'],
                'change': change,
                'changePercent': change_percent,
                'open': latest_data['open'],
                'high': latest_data['high'],
                'low': latest_data['low'],
                'volume': latest_data['volume']
            })
            
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)