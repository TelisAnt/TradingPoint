from django.core.management.base import BaseCommand
from django.db import connection
import psycopg2
from psycopg2 import sql
from django.conf import settings
from django.contrib.auth.hashers import make_password
from datetime import datetime

class Command(BaseCommand):
    help = 'Initializes the PostgreSQL database and creates USERS table with admin'

    def handle(self, *args, **options):
        # Database configuration
        db_config = {
            'NAME': 'TradingUsersdb',
            'USER': settings.DATABASES['default']['USER'],
            'PASSWORD': settings.DATABASES['default']['PASSWORD'],
            'HOST': settings.DATABASES['default']['HOST'],
            'PORT': settings.DATABASES['default']['PORT']
        }
        
        try:
            # Connect to PostgreSQL server
            conn = psycopg2.connect(
                user='postgres',
                password='password123',
                host=db_config['HOST'],
                port=db_config['PORT']
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                sql.SQL("SELECT 1 FROM pg_database WHERE datname = {}")
                .format(sql.Literal(db_config['NAME']))
            )
            exists = cursor.fetchone()

            if not exists:
                # Create database
                self.stdout.write(f"Creating database {db_config['NAME']}...")
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} ENCODING 'UTF8'")
                    .format(sql.Identifier(db_config['NAME']))
                )
                self.stdout.write(self.style.SUCCESS('Database created successfully'))
                
                # Now connect to the new database to create tables
                new_conn = psycopg2.connect(
                    dbname=db_config['NAME'],
                    user=db_config['USER'],
                    password=db_config['PASSWORD'],
                    host=db_config['HOST'],
                    port=db_config['PORT']
                )
                new_cursor = new_conn.cursor()
                
                # Create USERS table with admin fields
                new_cursor.execute("""
                    CREATE TABLE IF NOT EXISTS USERS (
                        id SERIAL PRIMARY KEY,
                        firstname VARCHAR(100) NOT NULL,
                        lastname VARCHAR(100) NOT NULL,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        age INTEGER CHECK (age >= 18),
                        is_admin BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        last_login TIMESTAMP
                    )
                """)
                
                # Create default admin user
                admin_password = make_password('admin123')  # Hashed password
                new_cursor.execute("""
                    INSERT INTO USERS 
                    (firstname, lastname, username, password, email, age, is_admin, is_active, last_login)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                """, (
                    'Admin',
                    'User',
                    'admin',
                    admin_password,
                    'admin@trading.com',
                    30,
                    True,
                    True,
                    datetime.now()
                ))
                
                new_conn.commit()
                self.stdout.write(self.style.SUCCESS('USERS table created successfully'))
                self.stdout.write(self.style.SUCCESS('Admin user created: username=admin, password=admin123'))
                
                # Create extensions if needed
                new_cursor.execute("CREATE EXTENSION IF NOT EXISTS hstore")
                new_cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
                new_conn.commit()
                
            else:
                self.stdout.write('Database already exists')
                # Connect to the TradingUsersdb database
                new_conn = psycopg2.connect(
                    dbname=db_config['NAME'], 
                    user=db_config['USER'],
                    password=db_config['PASSWORD'],
                    host=db_config['HOST'],
                    port=db_config['PORT']
                )
                new_cursor = new_conn.cursor()
                
                # First check if table exists
                new_cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'users'
                    )
                """)
                table_exists = new_cursor.fetchone()[0]
                
                if not table_exists:
                    self.stdout.write("Creating USERS table...")
                    new_cursor.execute("""
                        CREATE TABLE USERS (
                            id SERIAL PRIMARY KEY,
                            firstname VARCHAR(100) NOT NULL,
                            lastname VARCHAR(100) NOT NULL,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            password VARCHAR(255) NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            age INTEGER CHECK (age >= 18),
                            is_admin BOOLEAN DEFAULT FALSE,
                            is_active BOOLEAN DEFAULT TRUE,
                            last_login TIMESTAMP
                        )
                    """)
                    new_conn.commit()
                    self.stdout.write(self.style.SUCCESS('USERS table created'))
                
                # Now insert admin user
                admin_password = make_password('admin123')
                new_cursor.execute("""
                    INSERT INTO USERS 
                    (firstname, lastname, username, password, email, age, is_admin, is_active, last_login)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                """, (
                    'Admin',
                    'User',
                    'admin',
                    admin_password,
                    'admin@trading.com',
                    30,
                    True,
                    True,
                    datetime.now()
                ))
                new_conn.commit()
                
                if new_cursor.rowcount > 0:
                    self.stdout.write(self.style.SUCCESS('Admin user created'))
                else:
                    self.stdout.write('Admin user already exists')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
        finally:
            if 'conn' in locals():
                conn.close()
            if 'new_conn' in locals():
                new_conn.close()