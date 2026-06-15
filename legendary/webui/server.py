#!/usr/bin/env python3
# coding: utf-8

import logging
import os

from flask import Flask, jsonify, request, render_template, abort

from legendary.core import LegendaryCore

logger = logging.getLogger('webui')

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_SORT_KEYS'] = False

_core: LegendaryCore = None


def get_core() -> LegendaryCore:
    global _core
    if _core is None:
        _core = LegendaryCore()
    return _core


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.route('/api/auth/status')
def auth_status():
    core = get_core()
    try:
        logged_in = core.login()
        user = core.lgd.userdata.get('display_name', 'unknown') if logged_in else None
        return jsonify({'logged_in': logged_in, 'user': user})
    except Exception as e:
        return jsonify({'logged_in': False, 'user': None, 'error': str(e)})


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------

@app.route('/api/games')
def list_games():
    core = get_core()
    try:
        games, dlcs = core.get_game_and_dlc_list(update_assets=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    result = []
    installed_names = {g.app_name for g in core.get_installed_list()}
    for game in sorted(games, key=lambda g: g.app_title.lower()):
        result.append({
            'app_name': game.app_name,
            'title': game.app_title,
            'installed': game.app_name in installed_names,
        })
    return jsonify(result)


@app.route('/api/games/installed')
def list_installed():
    core = get_core()
    try:
        games = core.get_installed_list()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    result = []
    for game in sorted(games, key=lambda g: g.title.lower()):
        result.append({
            'app_name': game.app_name,
            'title': game.title,
            'version': game.version,
            'install_path': game.install_path,
            'install_size': game.install_size,
            'platform': game.platform,
        })
    return jsonify(result)


@app.route('/api/games/<app_name>')
def game_info(app_name):
    core = get_core()
    try:
        game = core.get_game(app_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 404
    if not game:
        abort(404)

    installed = core.get_installed_game(app_name)
    return jsonify({
        'app_name': game.app_name,
        'title': game.app_title,
        'installed': installed is not None,
        'install_path': installed.install_path if installed else None,
        'version': installed.version if installed else None,
        'install_size': installed.install_size if installed else None,
    })


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

@app.route('/api/status')
def status():
    from legendary import __version__, __codename__
    return jsonify({
        'version': __version__,
        'codename': __codename__,
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(host='127.0.0.1', port=6767, debug=False):
    logging.basicConfig(
        format='[%(name)s] %(levelname)s: %(message)s',
        level=logging.DEBUG if debug else logging.INFO,
    )
    logger.info(f'Starting legendary web UI on http://{host}:{port}')
    app.run(host=host, port=port, debug=debug)
