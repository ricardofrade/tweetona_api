from flask import jsonify, request
from pymongo import DESCENDING

from app import app, mongo
from .tasks import fetch_user_timeline


@app.errorhandler(404)
def route_not_found(e):
    return jsonify({'status': 404, 'message:': 'Route not found'}), 404


@app.route('/user/<string:name>', methods=['GET'])
def get_user(name):
    pipeline = [
        {'$match': {'user.screen_name': name}},
        {'$sort': {'id': DESCENDING}},
        {'$limit': 1},
        {'$replaceRoot': {'newRoot': '$user'}}
    ]
    cursor = mongo.db.tweets.aggregate(pipeline)
    data = cursor.next()
    if data:
        oldest = data['id']
        fetch_user_timeline.delay(name, oldest)
        return jsonify({'status': 200, 'data': data}), 200
    else:
        fetch_user_timeline.delay(name, -1)
        return jsonify({'status': 404, 'message:': 'User not found'}), 404


@app.route('/user/<string:name>/timeline', methods=['GET'])
def get_user_timeline(name):
    offset = request.args.get('offset', type=int)
    limit = request.args.get('limit', type=int)
    pipeline = [
        {'$match': {'user.screen_name': name}},
        {'$sort': {'id': DESCENDING}},
        {'$project': {'_id': 0, 'user': 0}}
    ]
    if offset:
        pipeline.append({'$skip': offset})
    if limit:
        pipeline.append({'$limit': limit})
    cursor = mongo.db.tweets.aggregate(pipeline)
    data_list = list(cursor)
    total = len(data_list)
    if total > 0:
        oldest = data_list[0]['id']
        fetch_user_timeline.delay(name, oldest)
        return jsonify({'status': 200, 'total': total, 'data': data_list}), 200
    else:
        fetch_user_timeline.delay(name, -1)
        return jsonify({'status': 404, 'message:': 'User not found'}), 404
