from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
class Command(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Command {self.command}>'

with app.app_context():
    db.create_all()

@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/scratchpad.html")
def scratchpad() -> str:
    return render_template("scratchpad.html")


@app.route("/calculator.html")
def calculator() -> str:
    return render_template("calculator.html")


@app.route("/password.html")
def password() -> str:
    return render_template("password.html")

# Route to store commands sent from the frontend
@app.route("/store_command", methods=["POST"])
def store_command():
    command_data = request.json  # Get JSON data from the frontend
    new_command = Command(command=command_data['command'])  # Create a new Command instance
    db.session.add(new_command)  # Add the command to the session
    db.session.commit()  # Commit the session to the database
    return jsonify({'status': 'success', 'command': command_data['command']}), 201


# Route to retrieve all commands (for testing/debugging)
@app.route("/commands", methods=["GET"])
def get_commands():
    commands = Command.query.all()  # Query all commands from the database
    return jsonify([{'id': c.id, 'command': c.command} for c in commands])  # Return as JSON



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4399)
