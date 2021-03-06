# encoding: utf-8

from __future__ import absolute_import

import csv
import datetime
import json
import six

from auth.constants import ROLES
from auth.models import Role, Network, Gateway, Voucher, Country, Currency, Product, db, users
from auth.services import manager
from flask import current_app
from flask_script import prompt, prompt_pass
from flask_security.utils import encrypt_password
from sqlalchemy import func


@manager.command
def bootstrap_instance(users_csv=None):
    db.create_all()

    create_roles()

    if users_csv:
        with open(users_csv) as f:
            for user in csv.reader(f):
                email, password, role = user
                create_user(email, password, role)


@manager.command
def bootstrap_tests():
    bootstrap_instance()

    create_network(u'main-network', u'Network')
    create_network(u'other-network', u'Other Network')

    create_gateway(u'main-network', u'main-gateway1', u'Main Gateway #1')
    create_gateway(u'main-network', u'main-gateway2', u'Main Gateway #2')

    create_gateway(u'other-network', u'other-gateway1', u'Other Gateway #1')
    create_gateway(u'other-network', u'other-gateway2', u'Other Gateway #2')

    create_user(u'super-admin@example.com', u'admin', u'super-admin')

    create_user(u'main-network@example.com', u'admin', u'network-admin', u'main-network')
    create_user(u'other-network@example.com', u'admin', u'network-admin', u'other-network')

    create_user(u'main-gateway1@example.com', u'admin', u'gateway-admin', u'main-network', u'main-gateway1')
    create_user(u'main-gateway2@example.com', u'admin', u'gateway-admin', u'main-network', u'main-gateway2')

    create_user(u'other-gateway1@example.com', u'admin', u'gateway-admin', u'other-network', u'other-gateway1')
    create_user(u'other-gateway2@example.com', u'admin', u'gateway-admin', u'other-network', u'other-gateway2')

    create_voucher(u'main-gateway1', 60, 'main-1-1')
    create_voucher(u'main-gateway1', 60, 'main-1-2')
    create_voucher(u'main-gateway2', 60, 'main-2-1')
    create_voucher(u'main-gateway2', 60, 'main-2-2')
    create_voucher(u'other-gateway1', 60, 'other-1-1')
    create_voucher(u'other-gateway1', 60, 'other-1-2')
    create_voucher(u'other-gateway2', 60, 'other-2-1')
    create_voucher(u'other-gateway2', 60, 'other-2-2')

    create_country(u'ZA', u'South Africa')
    create_currency(u'ZA', u'ZAR', u'South Africa', u'R')

    create_product(u'main-network', None, u'90MIN', u'90 Minute Voucher', 'ZAR', 3000, 'available')


@manager.command
def create_product(network_id, gateway_id, code, title, currency_id, price, status='new', quiet=True):
    product = Product()

    product.network_id = network_id
    product.gateway_id = gateway_id
    product.code = code
    product.title = title
    product.currency_id = currency_id
    product.price = price
    product.status = status

    db.session.add(product)
    db.session.commit()

    if not quiet:
        print('Product created: %s - %s' % (product.id, product.title))


@manager.command
def create_country(id, title, quiet=True):
    country = Country()

    country.id = id
    country.title = title

    db.session.add(country)
    db.session.commit()

    if not quiet:
        print('Country created: %s' % country.id)


@manager.command
def create_currency(country_id, id, title, prefix=None, suffix=None, quiet=True):
    currency = Currency()

    currency.country_id = country_id
    currency.id = id
    currency.title = title
    currency.prefix = prefix
    currency.suffix = suffix

    db.session.add(currency)
    db.session.commit()

    if not quiet:
        print('Currency created: %s' % currency.id)


@manager.command
def create_voucher(gateway, minutes=60, code=None, quiet=True):
    voucher = Voucher()

    # Allow explicit setting of code (for tests)
    if code is not None:
        voucher.code = code

    voucher.gateway_id = gateway
    voucher.minutes = minutes

    db.session.add(voucher)
    db.session.commit()

    if not quiet:
        print('Voucher created: %s:%s' % (voucher.id, voucher.code))


@manager.command
def create_network(id, title, description=None, quiet=True):
    network = Network()
    network.id = id
    network.title = title
    network.description = description
    db.session.add(network)
    db.session.commit()

    if not quiet:
        print('Network created')


@manager.command
@manager.option('-e', '--email', help='Contact Email')
@manager.option('-p', '--phone', help='Contact Phone')
@manager.option('-h', '--home', help='Home URL')
@manager.option('-f', '--facebook', help='Facebook URL')
def create_gateway(network, id, title, description=None, email=None, phone=None, home=None, facebook=None, logo=None, quiet=True):
    gateway = Gateway()
    gateway.network_id = network
    gateway.id = id
    gateway.title = title
    gateway.description = description
    gateway.contact_email = email
    gateway.contact_phone = phone
    gateway.url_home = home
    gateway.url_facebook = facebook
    db.session.add(gateway)
    db.session.commit()

    if not quiet:
        print('Gateway created')


@manager.command
def create_user(email, password, role, network=None, gateway=None, confirmed=True, quiet=True):
    if email is None:
        email = prompt('Email')

    if password is None:
        password = prompt_pass('Password')
        confirmation = prompt_pass('Confirm Password')

        if password != confirmation:
            print("Passwords don't match")
            return

    if role == 'network-admin':
        if network is None:
            print('Network is required for a network admin')
            return
        if gateway is not None:
            print('Gateway is not required for a network admin')
            return

    if role == 'gateway-admin':
        if network is None:
            print('Network is required for a gateway admin')
            return
        if gateway is None:
            print('Gateway is required for a gateway admin')
            return

    user = users.create_user(email=email, password=encrypt_password(password))

    user.network_id = network
    user.gateway_id = gateway

    if confirmed:
        user.confirmed_at = datetime.datetime.now()

    if role is not None:
        role = Role.query.filter_by(name=role).first()
        user.roles.append(role)

    db.session.commit()

    if not quiet:
        print('User created')


@manager.command
def auth_token(email):
    return users.get_user(email).get_auth_token()


@manager.command
def create_roles(quiet=True):
    if Role.query.count() == 0:
        for name, description in six.iteritems(ROLES):
            create_role(name, description, quiet)
        if not quiet:
            print('Roles created')


@manager.command
def create_role(name, description, quiet=True):
    role = users.create_role(name=name, description=description)
    db.session.add(role)
    db.session.commit()
    if not quiet:
        print('Role created')


@manager.command
def process_vouchers():
    # Active vouchers that should end
    vouchers = Voucher.query \
                .filter(Voucher.status == 'active') \
                .all()

    for voucher in vouchers:
        if voucher.should_end():
            voucher.end()
            db.session.add(voucher)

    # New vouchers that are unused and should expire
    max_age = current_app.config.get('VOUCHER_MAXAGE', 120)
    vouchers = Voucher.query \
                .filter(Voucher.status == 'new') \
                .all()

    for voucher in vouchers:
        if voucher.should_expire():
            voucher.expire()
            db.session.add(voucher)

    # Blocked, ended and expired vouchers that should be archived
    vouchers = Voucher.query \
                .filter(Voucher.updated_at + datetime.timedelta(minutes=max_age) < func.current_timestamp()) \
                .filter(Voucher.status.in_([ 'blocked', 'ended', 'expired' ])) \
                .all()

    for voucher in vouchers:
        voucher.archive()
        db.session.add(voucher)

    db.session.commit()


@manager.command
def measurements():
    (incoming, outgoing) = db.session.query(func.sum(Voucher.incoming), func.sum(Voucher.outgoing)).filter(Voucher.status == 'active').first()

    measurements = {
        'vouchers': {
            'active': Voucher.query.filter_by(status='active').count(),
            'blocked': Voucher.query.filter_by(status='blocked').count(),
            'incoming': incoming,
            'outgoing': outgoing,
            # 'both': incoming + outgoing,
        }
    }

    print(json.dumps(measurements, indent=4))
