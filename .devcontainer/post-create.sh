#!/bin/bash
set -euo pipefail

echo "🔧 Running post-create setup for Kettlewright..."

# Ensure we're in the workspace directory
cd /workspace

# Dependencies, including test tools, are installed in Dockerfile.dev.
# Rebuild the image when requirements.txt changes.

# Create instance directory with proper permissions
echo "📁 Creating instance directory..."
mkdir -p /workspace/instance

# Compile translations (if needed)
echo "🌍 Compiling translations..."
if [ -d "/workspace/app/translations" ]; then
    pybabel compile -d app/translations
fi

# Apply pending migrations to the database configured in .env.
# Loading the Flask application also builds its static assets.
echo "🗄️  Applying migrations and building static assets..."
flask db upgrade

# Display success message
echo "✅ Post-create setup complete!"
echo ""
echo "Docker Compose starts Flask automatically after this script."
echo "Inside an IDE-managed Dev Container, start it with F5 or:"
echo "  flask run --host=0.0.0.0 --port=8000"
echo ""
echo "Or run tests with:"
echo "  pytest"
