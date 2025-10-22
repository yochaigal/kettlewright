#!/bin/bash
set -e

echo "🔧 Running post-create setup for Kettlewright..."

# Ensure we're in the workspace directory
cd /workspace

# Install Python dependencies (in case requirements changed)
echo "📦 Installing Python dependencies..."
pip install --no-cache-dir pipenv
pipenv install --dev --system

# Create instance directory with proper permissions
echo "📁 Creating instance directory..."
mkdir -p /workspace/instance

# Set up the database
echo "🗄️  Setting up database..."
if [ ! -f "/workspace/instance/kettlewright.db" ]; then
    echo "Creating new database..."
    flask db upgrade
else
    echo "Database exists, running migrations..."
    flask db upgrade
fi

# Compile translations (if needed)
echo "🌍 Compiling translations..."
if [ -d "/workspace/app/translations" ]; then
    pybabel compile -d app/translations || echo "No translations to compile"
fi

# Build static assets
echo "🎨 Building static assets..."
if [ -f "/workspace/app/assets.py" ]; then
    python -c "from app import create_app; app = create_app(); app.app_context().push(); from flask_assets import Environment; from app.assets import bundles; assets = Environment(app); assets.register(bundles)" || echo "Asset compilation skipped"
fi

# Display success message
echo "✅ Post-create setup complete!"
echo ""
echo "You can now run the application with:"
echo "  flask run --host=0.0.0.0 --port=8000"
echo ""
echo "Or run tests with:"
echo "  pytest"
