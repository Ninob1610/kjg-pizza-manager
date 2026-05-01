#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Set environment variables for local development/RPi (no SSL required)
export SECURE_SSL_REDIRECT=0
export DEBUG=False

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Apply migrations
echo "Applying database migrations..."
python manage.py migrate

# Create default admin user
echo "Checking for default admin user..."
python manage.py create_default_admin

# Create or update the default pizza products
echo "Checking default pizza products..."
python manage.py create_default_products

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the server using Gunicorn
# Binding to 0.0.0.0 to make it accessible on the network
echo "Starting KjG Pizza Server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
