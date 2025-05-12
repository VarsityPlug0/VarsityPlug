# Varsity Plug

A comprehensive university application management system that helps students apply to South African universities.

## Features

- University application management
- APS score calculation
- Document upload and management
- Subscription-based services
- AI-powered chat assistance
- Application fee guidance
- Course recommendations
- WhatsApp support integration
- Concierge service for premium users

## Tech Stack

- Django 5.0.2
- Redis for caching and rate limiting
- PostgreSQL for production
- SQLite for development
- OpenAI API for chat assistance
- WhiteNoise for static files

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/varsity_plug.git
cd varsity_plug
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a .env file with:
```
DEBUG=True
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key
```

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Subscription Packages

- Basic Package (R400): Up to 3 university applications
- Standard Package (R600): Up to 5 applications + Fee Guidance
- Premium Package (R800): Up to 7 applications + Course Advice + WhatsApp Support
- Ultimate Package (R1000): Unlimited applications + Full Concierge Service

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
