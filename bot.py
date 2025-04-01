import os
import re
import json
from pathlib import Path
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

# Load environment variables (Recommended: store tokens securely)
SLACK_BOT_TOKEN = "xoxb-7928080676147-8700935802129-MxY1XzjLZmUU9UBR6gTw3qCi"  # Replace with your actual bot token
SLACK_SIGNING_SECRET = "eef970c341fcb6aa4e26aa5eccb51a82"  # Replace with your actual signing secret

# Initialize the Slack app
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

# Create Flask app
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

# File to store aura points
AURA_FILE = "aura_points.json"

def load_aura_points():
    """Load aura points from file or initialize if not exists"""
    if Path(AURA_FILE).exists():
        with open(AURA_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_aura_points(aura_points):
    """Save aura points to file"""
    with open(AURA_FILE, 'w') as file:
        json.dump(aura_points, file)

@app.event("app_mention")
def handle_app_mentions(body, say):
    """Handle mentions of the bot"""
    text = body["event"]["text"]
    channel_id = body["event"]["channel"]
    
    # Extract the user who was mentioned
    user_pattern = r"<@([A-Z0-9]+)>\s+(?:gained|lost)\s+\d+\s+aura"
    user_match = re.search(user_pattern, text)
    
    if not user_match:
        say("Invalid command. Use '@username gained 50 aura' or '@username lost 20 aura'.")
        return
    
    target_user_id = user_match.group(1)
    
    action_pattern = r"(gained|lost)\s+(\d+)\s+aura"
    action_match = re.search(action_pattern, text)
    
    if not action_match:
        say("Invalid format. Use '@username gained 50 aura' or '@username lost 20 aura'.")
        return
    
    action = action_match.group(1)
    amount = int(action_match.group(2))
    
    # Load current aura points
    aura_points = load_aura_points()
    
    # Initialize user if not exists
    if target_user_id not in aura_points:
        aura_points[target_user_id] = 0
    
    # Update aura points
    if action == "gained":
        aura_points[target_user_id] += amount
    else:
        aura_points[target_user_id] -= amount
    
    save_aura_points(aura_points)
    say(f"<@{target_user_id}> now has {aura_points[target_user_id]} aura.")

@app.command("/aurameter")
def handle_aurameter_command(ack, command, say):
    """Handle /aurameter slash command"""
    ack()
    
    args = command["text"].split()
    
    aura_points = load_aura_points()
    
    if not args or args[0] == "help":
        say("Aurameter commands:\n"
            "/aurameter status - Show everyone's aura points\n"
            "/aurameter top - Show top 5 users with most aura\n"
            "/aurameter bottom - Show bottom 5 users with least aura\n"
            "/aurameter @username - Show specific user's aura points")
        return
    
    if args[0] == "status":
        if not aura_points:
            say("No one has any aura points yet!")
            return
        
        response = "Current Aura Points:\n"
        for user_id, points in sorted(aura_points.items(), key=lambda x: x[1], reverse=True):
            response += f"<@{user_id}>: {points} aura\n"
        
        say(response)
    
    elif args[0] == "top":
        if not aura_points:
            say("No one has any aura points yet!")
            return
        
        top_users = sorted(aura_points.items(), key=lambda x: x[1], reverse=True)[:5]
        
        response = "Top Aura Leaders:\n"
        for i, (user_id, points) in enumerate(top_users, 1):
            response += f"{i}. <@{user_id}>: {points} aura\n"
        
        say(response)
    
    elif args[0] == "bottom":
        if not aura_points:
            say("No one has any aura points yet!")
            return
        
        bottom_users = sorted(aura_points.items(), key=lambda x: x[1])[:5]
        
        response = "Bottom Aura Holders:\n"
        for i, (user_id, points) in enumerate(bottom_users, 1):
            response += f"{i}. <@{user_id}>: {points} aura\n"
        
        say(response)
    
    elif args[0].startswith("<@") and args[0].endswith(">"):
        # Get user's aura
        user_id = args[0][2:-1]
        points = aura_points.get(user_id, 0)
        say(f"<@{user_id}> has {points} aura points.")
    
    else:
        say("Unknown command. Try /aurameter help for available commands.")

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """Slack event listener"""
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(port=3000)
