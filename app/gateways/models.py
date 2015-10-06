import datetime

from app import db, api_manager
from flask.ext.restless import ProcessingException
from flask.ext.security import current_user
from marshmallow import Schema, fields

class Gateway(db.Model):
    __tablename__ = 'gateways'

    id = db.Column(db.Unicode, primary_key=True)
    network_id = db.Column(db.Unicode, db.ForeignKey('networks.id'))

    title = db.Column(db.Unicode, nullable=False)
    description = db.Column(db.Unicode, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)

class GatewaySchema(Schema):
    id = fields.Str()
    network_id = fields.Str()
    title = fields.Str()
    description = fields.Str()
    created_at = fields.DateTime()

    def make_object(self, data):
        return Gateway(**data)

def preprocess_many(search_params=None, **kwargs):
    if search_params is None:
        search_params = {}

    if 'filters' not in search_params:
        search_params['filters'] = []

    if current_user.has_role('network-admin'):
        search_params['filters'].append(dict(name='network_id', op='eq', val=current_user.network_id))

    if current_user.has_role('gateway-admin'):
        raise ProcessingException(description='Not Authorized', code=401)

def preprocess_single(instance_id=None, **kwargs):
    if instance_id is None:
        return

    if current_user.has_role('super-admin'):
        return

    gateway = Gateway.query.get(instance_id)

    if (current_user.has_role('network-admin')
            and gateway.network_id == current_user.network_id):
        return

    raise ProcessingException(description='Not Authorized', code=401)

api_manager.create_api(Gateway,
        collection_name='gateways',
        methods=[ 'GET', 'POST', 'DELETE' ],
        preprocessors=dict(
            GET_SINGLE=[preprocess_single],
            GET_MANY=[preprocess_many],
            POST=[preprocess_single],
            DELETE_SINGLE=[preprocess_single],
        ))