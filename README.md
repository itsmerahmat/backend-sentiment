# Sentiment Analysis API - Backend

A FastAPI backend for Instagram sentiment analysis with dual sentiment analysis methods (IndoBERT Deep Learning & Lexicon-based) and Apify integration for data scraping.

## Features

- 🔐 **User Authentication** - JWT-based authentication with bcrypt password hashing
- 📊 **Instagram Data Management** - Store and manage Instagram accounts, posts, and comments
- 🤖 **Apify Integration** - Scrape Instagram data using Apify actors
- 🧠 **IndoBERT Sentiment Analysis** - Deep learning-based sentiment analysis using fine-tuned IndoBERT model (ONNX)
- 📖 **Lexicon Sentiment Analysis** - Rule-based sentiment analysis using Indonesian word dictionary (10,000+ words)
- 🗃️ **PostgreSQL Database** - Robust data storage with SQLModel ORM
- 🔄 **Database Migrations** - Alembic for schema versioning
- ⚛️ **React SPA Support** - Serve React build as static files

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── dependencies.py         # Shared dependencies (DB session, auth)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Application settings
│   │   └── security.py         # Password hashing, JWT tokens
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py         # Database engine and session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── enums.py            # Enum definitions (UserRole, SentimentLabel)
│   │   ├── user.py             # User SQLModel
│   │   ├── ig_account.py       # Instagram Account SQLModel
│   │   ├── ig_post.py          # Instagram Post SQLModel
│   │   └── ig_comment.py       # Instagram Comment SQLModel
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── ig_account.py       # Instagram Account schemas
│   │   ├── ig_post.py          # Instagram Post schemas
│   │   ├── ig_comment.py       # Instagram Comment schemas
│   │   ├── indobert.py         # IndoBERT sentiment schemas
│   │   └── lexicon.py          # Lexicon sentiment schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py     # User business logic
│   │   ├── ig_account_service.py   # Instagram Account service
│   │   ├── ig_post_service.py      # Instagram Post service
│   │   ├── ig_comment_service.py   # Instagram Comment service
│   │   ├── apify_service.py        # Apify integration service
│   │   ├── indobert_service.py     # IndoBERT sentiment service
│   │   └── lexicon_service.py      # Lexicon sentiment service
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py            # User API endpoints
│   │   ├── ig_accounts.py      # Instagram Account endpoints
│   │   ├── ig_posts.py         # Instagram Post endpoints
│   │   ├── ig_comments.py      # Instagram Comment endpoints
│   │   ├── indobert_sentiment.py   # IndoBERT sentiment endpoints
│   │   └── lexicon_sentiment.py    # Lexicon sentiment endpoints
│   ├── sentiment/
│   │   ├── indobert_model/     # Fine-tuned IndoBERT ONNX model
│   │   │   ├── model.onnx
│   │   │   ├── tokenizer_config.json
│   │   │   ├── vocab.txt
│   │   │   └── special_tokens_map.json
│   │   └── lexicon_based/      # Lexicon dictionaries
│   │       ├── kamus_positif.csv   # ~3,880 positive words
│   │       └── kamus_negatif.csv   # ~6,197 negative words
│   └── internal/
│       ├── __init__.py
│       └── admin.py            # Admin endpoints
├── static/                     # React build output
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_users.py
├── .env
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

## Installation

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sentiment_db

# JWT Settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Apify
APIFY_API_TOKEN=your-apify-token-here
```

## Running the Application

### Development
```bash
fastapi dev app/main.py
```

### Production
```bash
fastapi run app/main.py
```

## API Documentation

Once the application is running, you can access:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API Endpoints

All endpoints are prefixed with `/api`.

### Authentication
- `POST /api/users/register` - Register a new user
- `POST /api/users/login` - Login and get access token

### Users
- `GET /api/users/me` - Get current user info
- `GET /api/users/` - Get all users (requires auth)
- `GET /api/users/{user_id}` - Get user by ID (requires auth)
- `PUT /api/users/{user_id}` - Update user (requires auth)
- `DELETE /api/users/{user_id}` - Delete user (requires auth)

### Instagram Accounts
- `GET /api/ig-accounts/` - Get all Instagram accounts
- `POST /api/ig-accounts/` - Create Instagram account
- `GET /api/ig-accounts/{account_id}` - Get account by ID
- `PUT /api/ig-accounts/{account_id}` - Update account
- `DELETE /api/ig-accounts/{account_id}` - Delete account

### Instagram Posts
- `GET /api/ig-posts/` - Get all posts
- `POST /api/ig-posts/` - Create post
- `GET /api/ig-posts/{post_id}` - Get post by ID
- `PUT /api/ig-posts/{post_id}` - Update post
- `DELETE /api/ig-posts/{post_id}` - Delete post

### Instagram Comments
- `GET /api/ig-comments/` - Get all comments
- `POST /api/ig-comments/` - Create comment
- `GET /api/ig-comments/{comment_id}` - Get comment by ID
- `PUT /api/ig-comments/{comment_id}` - Update comment
- `DELETE /api/ig-comments/{comment_id}` - Delete comment

### IndoBERT Sentiment Analysis
- `GET /api/indobert/health` - Check if IndoBERT model is loaded
- `POST /api/indobert/predict` - Batch sentiment prediction
- `POST /api/indobert/predict/single` - Single text sentiment prediction
- `POST /api/indobert/analyze-post/{post_id}` - Analyze all comments on a post (requires auth)

### Lexicon Sentiment Analysis
- `GET /api/lexicon/health` - Check lexicon service status
- `GET /api/lexicon/lexicon-words` - Get all words in dictionary
- `POST /api/lexicon/predict` - Batch sentiment prediction
- `POST /api/lexicon/predict/single` - Single text sentiment prediction
- `POST /api/lexicon/analyze-post/{post_id}` - Analyze all comments on a post (requires auth)

### Admin
- `GET /api/admin/dashboard` - Admin dashboard (requires auth)
- `GET /api/admin/stats` - Application statistics (requires auth)

### Health
- `GET /health` - Health check

## Sentiment Analysis Methods

### 1. IndoBERT (Deep Learning)
Uses a fine-tuned IndoBERT model converted to ONNX format for efficient inference without PyTorch dependency.

**Features:**
- Pre-trained on Indonesian language corpus
- Fine-tuned for sentiment classification
- Labels: Positif, Negatif, Netral
- Confidence score for each prediction

### 2. Lexicon-Based (Rule-Based)
Uses Indonesian word dictionaries with sentiment weights for rule-based classification.

**Features:**
- 3,880+ positive words with weights
- 6,197+ negative words with weights
- Negation handling (tidak, bukan, etc.)
- Sastrawi stemming & stopword removal
- Matched words tracking for explainability

## Running Tests

```bash
pytest
```

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL databases with Pydantic models
- **PostgreSQL** - Database
- **Alembic** - Database migrations
- **bcrypt** - Password hashing
- **python-jose** - JWT tokens
- **Apify** - Instagram data scraping
- **ONNX Runtime** - IndoBERT model inference
- **Transformers** - Tokenizer for IndoBERT
- **Sastrawi** - Indonesian NLP (stemming & stopword removal)

## Configuration

Environment variables can be configured in `.env`:

```env
# App Settings
APP_NAME=Sentiment API
APP_VERSION=1.0.0
DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sentiment_db

# JWT Settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Apify
APIFY_TOKEN=your-apify-token-here

# Model Paths (optional, has defaults)
INDOBERT_MODEL_DIR=app/sentiment/indobert_model
LEXICON_DIR=app/sentiment/lexicon_based
```

## License

MIT
