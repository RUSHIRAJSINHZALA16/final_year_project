from app import create_app

# This 'app' variable is what Flask-Migrate looks for
app = create_app()

if __name__ == "__main__":
    # Runs the server locally
    app.run(debug=True)