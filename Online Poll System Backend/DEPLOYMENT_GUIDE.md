# 🚀 Online Poll System - Deployment Guide

## 📋 Overview
This guide provides step-by-step instructions for deploying the Online Poll System Backend to various platforms including Heroku, Railway, and Render.

## 🛠️ Prerequisites
- Git repository with your code
- Python 3.11+
- PostgreSQL database
- Environment variables configured

## 🌐 Platform Deployment Options

### Option 1: Heroku Deployment (Recommended)

#### Step 1: Install Heroku CLI
```bash
# Download and install from https://devcenter.heroku.com/articles/heroku-cli
# Or using npm
npm install -g heroku
```

#### Step 2: Login and Create App
```bash
heroku login
heroku create your-poll-system-app
```

#### Step 3: Configure Environment Variables
```bash
heroku config:set SECRET_KEY="your-super-secret-key-here"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="your-poll-system-app.herokuapp.com"
heroku config:set DATABASE_URL="postgresql://..."  # Heroku will provide this
```

#### Step 4: Add PostgreSQL Add-on
```bash
heroku addons:create heroku-postgresql:mini
```

#### Step 5: Deploy
```bash
git add .
git commit -m "Prepare for deployment"
git push heroku main
```

#### Step 6: Run Migrations
```bash
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### Option 2: Railway Deployment

#### Step 1: Connect Repository
1. Go to [Railway](https://railway.app)
2. Connect your GitHub repository
3. Select the project

#### Step 2: Configure Environment Variables
Add these in Railway dashboard:
- `SECRET_KEY`: Your Django secret key
- `DEBUG`: False
- `ALLOWED_HOSTS`: your-app.railway.app
- `DATABASE_URL`: Will be auto-configured with PostgreSQL service

#### Step 3: Add PostgreSQL Service
1. Click "New Service" → "Database" → "PostgreSQL"
2. Railway will automatically configure DATABASE_URL

#### Step 4: Deploy
Railway will automatically deploy when you push to your connected branch.

### Option 3: Render Deployment

#### Step 1: Create Web Service
1. Go to [Render](https://render.com)
2. Connect your GitHub repository
3. Create a new Web Service

#### Step 2: Configure Build Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn poll_system.wsgi:application`
- **Python Version**: 3.11.7

#### Step 3: Environment Variables
Add in Render dashboard:
- `SECRET_KEY`: Your Django secret key
- `DEBUG`: False
- `DATABASE_URL`: Connection string from PostgreSQL service

#### Step 4: Add PostgreSQL Database
1. Create a new PostgreSQL service
2. Copy the connection string to `DATABASE_URL`

## 🔧 Environment Variables Template

Create a `.env` file (for local development) or set these in your hosting platform:

```env
# Django Configuration
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database Configuration (for local development)
DB_NAME=poll_system_db
DB_USER=postgres
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432

# Production Database (hosting platforms provide this)
DATABASE_URL=postgresql://user:password@host:port/database
```

## 🏗️ Post-Deployment Steps

### 1. Run Database Migrations
```bash
# For Heroku
heroku run python manage.py migrate

# For Railway/Render (usually automatic via Procfile)
python manage.py migrate
```

### 2. Create Superuser
```bash
# For Heroku
heroku run python manage.py createsuperuser

# For Railway/Render
python manage.py createsuperuser
```

### 3. Collect Static Files (if needed)
```bash
python manage.py collectstatic --noinput
```

### 4. Load Sample Data (Optional)
```bash
# For Heroku
heroku run python manage.py seed_polls

# For Railway/Render
python manage.py seed_polls
```

## 🔍 Testing Your Deployment

### 1. Health Check Endpoints
- **API Root**: `https://your-app.com/api/v1/`
- **API Documentation**: `https://your-app.com/api/docs/`
- **Admin Interface**: `https://your-app.com/admin/`

### 2. Basic API Tests
```bash
# List polls
curl https://your-app.com/api/v1/polls/

# Get statistics
curl https://your-app.com/api/v1/statistics/

# Create a poll (requires authentication)
curl -X POST https://your-app.com/api/v1/polls/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{
    "title": "Test Poll",
    "description": "Testing deployment",
    "options": [
      {"text": "Option 1", "order": 1},
      {"text": "Option 2", "order": 2}
    ]
  }'
```

## 🛡️ Security Considerations

### 1. Environment Variables
- Never commit sensitive data to version control
- Use strong, unique secret keys
- Set DEBUG=False in production
- Configure ALLOWED_HOSTS properly

### 2. Database Security
- Use SSL connections for database
- Regular backups
- Monitor for unusual activity

### 3. API Security
- Implement rate limiting
- Use HTTPS only
- Validate all inputs
- Monitor API usage

## 📊 Monitoring & Maintenance

### 1. Application Monitoring
- Monitor response times
- Track error rates
- Monitor database performance
- Set up alerts for downtime

### 2. Database Maintenance
- Regular backups
- Monitor disk usage
- Optimize slow queries
- Update statistics

### 3. Updates & Patches
- Keep dependencies updated
- Apply security patches promptly
- Test updates in staging first

## 🚨 Troubleshooting

### Common Issues:

#### 1. Static Files Not Loading
```python
# In settings.py, ensure:
STATIC_ROOT = BASE_DIR / 'staticfiles'
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
```

#### 2. Database Connection Errors
- Verify DATABASE_URL format
- Check firewall settings
- Ensure database service is running

#### 3. CORS Issues
```python
# In settings.py, update:
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "https://your-app.herokuapp.com",
]
```

#### 4. Migration Errors
```bash
# Reset migrations if needed (CAUTION: Data loss)
python manage.py migrate polls zero
python manage.py migrate
```

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test database connectivity
4. Review hosting platform documentation

---

## 🎉 Success!

Once deployed successfully, your Online Poll System will be accessible at:
- **API**: `https://your-app.com/api/v1/`
- **Documentation**: `https://your-app.com/api/docs/`
- **Admin**: `https://your-app.com/admin/`

Your API is now ready to handle poll creation, voting, and real-time results!
