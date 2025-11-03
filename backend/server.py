from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import random
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class TeamData(BaseModel):
    name: str
    logo: str
    score: int
    xg: float
    possession: int
    shots: int
    shots_on_target: int
    corners: int
    dangerous_attacks: int

class Match(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    home_team: TeamData
    away_team: TeamData
    minute: int
    status: str  # live, halftime, finished
    comeback_probability: float
    is_comeback_scenario: bool
    losing_team: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ComebackAlert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    team_name: str
    opponent: str
    score: str
    probability: float
    minute: int
    reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False

# Superteams that we monitor
SUPERTEAMS = [
    {"name": "Real Madrid", "logo": "https://media.api-sports.io/football/teams/541.png", "comeback_rate": 0.75},
    {"name": "Manchester City", "logo": "https://media.api-sports.io/football/teams/50.png", "comeback_rate": 0.78},
    {"name": "Bayern Munich", "logo": "https://media.api-sports.io/football/teams/157.png", "comeback_rate": 0.72},
    {"name": "PSG", "logo": "https://media.api-sports.io/football/teams/85.png", "comeback_rate": 0.68},
    {"name": "Barcelona", "logo": "https://media.api-sports.io/football/teams/529.png", "comeback_rate": 0.71},
    {"name": "Liverpool", "logo": "https://media.api-sports.io/football/teams/40.png", "comeback_rate": 0.74},
]

OPPONENTS = [
    {"name": "Atletico Madrid", "logo": "https://media.api-sports.io/football/teams/530.png"},
    {"name": "Sevilla", "logo": "https://media.api-sports.io/football/teams/536.png"},
    {"name": "Napoli", "logo": "https://media.api-sports.io/football/teams/489.png"},
    {"name": "Arsenal", "logo": "https://media.api-sports.io/football/teams/42.png"},
    {"name": "Inter Milan", "logo": "https://media.api-sports.io/football/teams/505.png"},
]

def calculate_comeback_probability(team_data: TeamData, opponent_data: TeamData, is_superteam: bool, comeback_rate: float) -> tuple[float, str]:
    """Calculate probability of comeback based on statistics"""
    probability = 0.0
    reasons = []
    
    # Base probability for superteams
    if is_superteam:
        probability += comeback_rate * 30
        reasons.append(f"Time com histórico de viradas ({int(comeback_rate*100)}%)")
    
    # xG advantage
    if team_data.xg > opponent_data.xg:
        xg_diff = team_data.xg - opponent_data.xg
        probability += min(xg_diff * 15, 25)
        reasons.append(f"xG superior ({team_data.xg:.1f} vs {opponent_data.xg:.1f})")
    
    # Possession
    if team_data.possession > 55:
        probability += (team_data.possession - 55) * 0.5
        reasons.append(f"Domínio de posse ({team_data.possession}%)")
    
    # Shots advantage
    if team_data.shots > opponent_data.shots:
        shot_diff = team_data.shots - opponent_data.shots
        probability += min(shot_diff * 2, 15)
        reasons.append(f"Mais finalizações ({team_data.shots} vs {opponent_data.shots})")
    
    # Shots on target
    if team_data.shots_on_target > opponent_data.shots_on_target:
        probability += min((team_data.shots_on_target - opponent_data.shots_on_target) * 3, 10)
    
    # Dangerous attacks
    if team_data.dangerous_attacks > opponent_data.dangerous_attacks:
        probability += min((team_data.dangerous_attacks - opponent_data.dangerous_attacks) * 0.3, 10)
        reasons.append("Alta pressão ofensiva")
    
    probability = min(probability, 95)
    reason = ", ".join(reasons[:3])
    
    return probability, reason

async def generate_mock_matches():
    """Generate mock live matches with superteams"""
    matches = []
    
    for i, superteam in enumerate(SUPERTEAMS[:4]):  # Generate 4 matches
        opponent = random.choice(OPPONENTS)
        minute = random.randint(15, 85)
        
        # Randomly decide if superteam is losing
        is_losing = random.random() > 0.5
        
        if is_losing:
            home_score = random.randint(0, 1)
            away_score = home_score + 1
        else:
            home_score = random.randint(1, 3)
            away_score = random.randint(0, home_score)
        
        # Generate statistics favoring the superteam if losing
        if is_losing:
            superteam_stats = TeamData(
                name=superteam["name"],
                logo=superteam["logo"],
                score=home_score,
                xg=round(random.uniform(1.5, 2.8), 1),
                possession=random.randint(58, 72),
                shots=random.randint(12, 20),
                shots_on_target=random.randint(5, 10),
                corners=random.randint(6, 12),
                dangerous_attacks=random.randint(45, 75)
            )
            opponent_stats = TeamData(
                name=opponent["name"],
                logo=opponent["logo"],
                score=away_score,
                xg=round(random.uniform(0.5, 1.2), 1),
                possession=100 - superteam_stats.possession,
                shots=random.randint(4, 8),
                shots_on_target=random.randint(2, 4),
                corners=random.randint(2, 5),
                dangerous_attacks=random.randint(15, 30)
            )
            
            probability, reason = calculate_comeback_probability(
                superteam_stats, opponent_stats, True, superteam["comeback_rate"]
            )
            
            match = Match(
                home_team=superteam_stats,
                away_team=opponent_stats,
                minute=minute,
                status="live",
                comeback_probability=probability,
                is_comeback_scenario=probability > 50,
                losing_team=superteam["name"]
            )
        else:
            superteam_stats = TeamData(
                name=superteam["name"],
                logo=superteam["logo"],
                score=home_score,
                xg=round(random.uniform(1.2, 2.5), 1),
                possession=random.randint(52, 68),
                shots=random.randint(10, 18),
                shots_on_target=random.randint(4, 9),
                corners=random.randint(5, 10),
                dangerous_attacks=random.randint(35, 60)
            )
            opponent_stats = TeamData(
                name=opponent["name"],
                logo=opponent["logo"],
                score=away_score,
                xg=round(random.uniform(0.4, 1.5), 1),
                possession=100 - superteam_stats.possession,
                shots=random.randint(5, 10),
                shots_on_target=random.randint(2, 5),
                corners=random.randint(3, 7),
                dangerous_attacks=random.randint(20, 40)
            )
            
            match = Match(
                home_team=superteam_stats,
                away_team=opponent_stats,
                minute=minute,
                status="live",
                comeback_probability=0,
                is_comeback_scenario=False,
                losing_team=None
            )
        
        matches.append(match)
    
    return matches

@api_router.get("/")
async def root():
    return {"message": "Comeback Scout API"}

@api_router.get("/matches/live", response_model=List[Match])
async def get_live_matches():
    """Get all live matches"""
    matches = await generate_mock_matches()
    return matches

@api_router.get("/matches/{match_id}", response_model=Match)
async def get_match(match_id: str):
    """Get specific match details"""
    matches = await generate_mock_matches()
    for match in matches:
        if match.id == match_id:
            return match
    raise HTTPException(status_code=404, detail="Match not found")

@api_router.get("/alerts", response_model=List[ComebackAlert])
async def get_alerts():
    """Get comeback alerts"""
    alerts = await db.comeback_alerts.find({}, {"_id": 0}).sort("timestamp", -1).to_list(50)
    
    for alert in alerts:
        if isinstance(alert['timestamp'], str):
            alert['timestamp'] = datetime.fromisoformat(alert['timestamp'])
    
    return alerts

@api_router.post("/alerts/mark-read/{alert_id}")
async def mark_alert_read(alert_id: str):
    """Mark alert as read"""
    result = await db.comeback_alerts.update_one(
        {"id": alert_id},
        {"$set": {"read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"success": True}

@api_router.post("/matches/check-comebacks")
async def check_and_create_alerts():
    """Check matches and create alerts for high comeback probability"""
    matches = await generate_mock_matches()
    alerts_created = 0
    
    for match in matches:
        if match.is_comeback_scenario and match.comeback_probability > 60:
            # Check if alert already exists for this match recently
            existing = await db.comeback_alerts.find_one({
                "match_id": match.id,
                "team_name": match.losing_team
            })
            
            if not existing:
                # Calculate reason
                losing_team_data = match.home_team if match.home_team.name == match.losing_team else match.away_team
                opponent_data = match.away_team if match.home_team.name == match.losing_team else match.home_team
                
                _, reason = calculate_comeback_probability(
                    losing_team_data, 
                    opponent_data, 
                    True, 
                    0.7
                )
                
                alert = ComebackAlert(
                    match_id=match.id,
                    team_name=match.losing_team,
                    opponent=opponent_data.name,
                    score=f"{match.home_team.score}-{match.away_team.score}",
                    probability=match.comeback_probability,
                    minute=match.minute,
                    reason=reason
                )
                
                doc = alert.model_dump()
                doc['timestamp'] = doc['timestamp'].isoformat()
                
                await db.comeback_alerts.insert_one(doc)
                alerts_created += 1
    
    return {"alerts_created": alerts_created}

@api_router.get("/superteams")
async def get_superteams():
    """Get list of monitored superteams"""
    return SUPERTEAMS

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()