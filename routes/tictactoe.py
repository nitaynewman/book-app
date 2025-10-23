from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from uuid import uuid4
import sqlite3
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
# import bcrypt

router = APIRouter(
    prefix="/tictactoe",
    tags=["TicTacToe"]
)

# Configuration
SECRET_KEY = "your_secret_key"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1

security = HTTPBearer()

# Database initialization
def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class MoveData(BaseModel):
    index: int

# Game storage
games = {}

class Game:
    def __init__(self):
        self.board = [""] * 9
        self.players = {}  # Changed to dict to track symbol per player
        self.turn = "X"  
        self.winner = None

    async def send_state(self):
        """Send game state to both players."""
        state = {"board": self.board, "turn": self.turn, "winner": self.winner}
        for websocket in self.players.keys():
            try:
                await websocket.send_json(state)
            except:
                pass

    def make_move(self, index, symbol):
        """Validate and make a move."""
        if self.board[index] == "" and self.turn == symbol and not self.winner:
            self.board[index] = symbol
            self.turn = "O" if self.turn == "X" else "X"
            self.check_winner()
            return True
        return False

    def check_winner(self):
        """Check if there's a winner."""
        win_patterns = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  
            [0, 4, 8], [2, 4, 6]            
        ]
        for pattern in win_patterns:
            a, b, c = pattern
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                self.winner = self.board[a]

# Helper functions
def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_access_token(data: dict):
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Authentication routes
@router.post("/register")
def register(user: UserRegister):
    """Register a new user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Hash the password with werkzeug
        hashed_password = generate_password_hash(user.password)
        
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (user.username, hashed_password)
        )
        conn.commit()
        conn.close()
        
        return {"message": "User registered successfully"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")

# Update the login function:
@router.post("/login")
def login(user: UserLogin):
    """Login user and return JWT token."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (user.username,))
    db_user = cursor.fetchone()
    conn.close()
    
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    # Verify password with werkzeug
    if not check_password_hash(db_user["password"], user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    # Create access token
    access_token = create_access_token(data={"username": user.username})
    
    return {
        "message": "Login successful",
        "token": access_token
    }


# Game routes
@router.get("/create-game")
def create_game(username: str = Depends(verify_token)):
    """Create a new game and return its ID. Requires authentication."""
    game_id = str(uuid4())
    games[game_id] = Game()
    return {"game_id": game_id}

@router.websocket("/ws/{game_id}")  # Remove symbol from URL
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """Handle WebSocket connections for players."""
    await websocket.accept()

    if game_id not in games:
        await websocket.send_json({"error": "Game not found"})
        await websocket.close()
        return

    game = games[game_id]

    if len(game.players) >= 2:
        await websocket.send_json({"error": "Game is full"})
        await websocket.close()
        return

    # Assign symbol based on order
    symbol = "X" if len(game.players) == 0 else "O"
    game.players[websocket] = symbol

    # Send initial state with player's symbol
    await websocket.send_json({
        "board": game.board,
        "turn": game.turn,
        "winner": game.winner,
        "yourSymbol": symbol
    })

    # If both players connected, notify both
    if len(game.players) == 2:
        await game.send_state()

    try:
        while True:
            data = await websocket.receive_json()
            index = data["index"]

            if game.make_move(index, symbol):
                await game.send_state()
    except WebSocketDisconnect:
        if websocket in game.players:
            del game.players[websocket]

