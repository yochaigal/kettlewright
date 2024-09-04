from flask_assets import Bundle, Environment


def compile_static_assets(app):
    assets = Environment(app)
    # Environment.auto_build = True
    # Environment.debug = False
    assets.auto_build = True
    assets.debug = False

    scss = Bundle('src/scss/magic.css/normalize.css', 'src/scss/magic.css/magick.css',
                  'src/scss/main.scss', 'src/scss/modals.scss', 'src/scss/inventory.scss',
                  'src/scss/create.scss', 'src/scss/character.scss', 'src/scss/characters-parties.scss', 'src/scss/party.scss', filters='libsass',
                  output='dist/css/style.css')
    assets.register('scss_all', scss)

    if app.config.get('FLASK_ENV') == 'development':
        print('Compiling static assets...')
        # assets.cache = False  # Disable the cache only in development mode
        # scss.build(force=True)
    scss.build()
