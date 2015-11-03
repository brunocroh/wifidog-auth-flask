import flask
import requests

from blinker import Namespace
from flask.ext.login import user_logged_in, user_logged_out

signals = Namespace()

voucher_generated = signals.signal('voucher_generated')
voucher_logged_in = signals.signal('voucher_logged_in')

def send_hit(t, data):
    data.update({
        'v': 1,
        'tid': flask.current_app.config['GOOGLE_ANALYTICS_TRACKING_ID'],
        'cid': flask.request.cookies.get('cid'),
        't': 'event',
    })

    requests.post('http://www.google-analytics.com/collect', data=data)

def send_event(category, action, label=None, value=None):
    send_hit('event', {
        'ec': category,
        'ea': action,
        'el': label,
        'ev': value,
    })

def on_user_logged_in(sender, user):
    flask.flash('You were logged in')
    send_event('security', 'login')

def on_user_logged_out(sender, user):
    flask.flash('You were logged out')
    send_event('security', 'logout')

def on_voucher_generated(sender, voucher):
    send_event('voucher', 'generate')

def on_voucher_logged_in(sender, voucher):
    flask.session['voucher_token'] = voucher.token
    send_event('voucher', 'login')

def init_signals(app):
    user_logged_in.connect(on_user_logged_in, app)
    user_logged_out.connect(on_user_logged_out, app)
    voucher_generated.connect(on_voucher_generated, app)
    voucher_logged_in.connect(on_voucher_logged_in, app)
