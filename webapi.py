import secrets
import hashlib
import pathlib
import uuid
import json
from pydub import AudioSegment
from flask import Flask, request, jsonify, send_file
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# Database setup
engine = create_engine('sqlite:///webapi.db')
Base = declarative_base()


class Token(Base):
    __tablename__ = 'tokens'
    access_token_hash = Column(String(64), nullable=False, primary_key=True)
    access_token_expired = Column(DateTime(timezone=True), nullable=False)
    refresh_token_hash = Column(String(64), nullable=False, unique=True)
    refresh_token_expired = Column(DateTime(timezone=True), nullable=False)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
app = Flask(__name__)


@app.route('/voicechange/api/token/create', methods=['POST'])
def __voicechange_api_token_fetch():

    # Get utc timestamp of now
    timestamp = datetime.now(timezone.utc)

    # Generate new Access-Token
    access_token_expired = timestamp + timedelta(minutes=30)
    access_token = secrets.token_bytes(32)
    access_token_hash = hashlib.sha256(access_token).hexdigest()

    # Make Query
    query = session.query(Token)\
        .filter_by(access_token_hash=access_token_hash)

    # Verification Access-Token
    while query.first():
        access_token = secrets.token_bytes(32)
        access_token_hash = hashlib.sha256(access_token).hexdigest()

    # Generate new Refresh-Token
    refresh_token_expired = timestamp + timedelta(days=7)
    refresh_token = secrets.token_bytes(32)
    refresh_token_hash = hashlib.sha256(refresh_token).hexdigest()

    # Make Query
    query = session.query(Token)\
        .filter_by(refresh_token_hash=refresh_token_hash)

    # Verification Refresh-Token
    while query.first():
        refresh_token = secrets.token_bytes(32)
        refresh_token_hash = hashlib.sha256(refresh_token).hexdigest()

    # Add token to table
    token = Token(
        access_token_expired=access_token_expired,
        access_token_hash=access_token_hash,
        refresh_token_expired=refresh_token_expired,
        refresh_token_hash=refresh_token_hash,
    )
    session.add(token)
    session.commit()

    # Return response
    return jsonify({
        'access_token': access_token.hex(),
        'access_token_expired': access_token_expired,
        'refresh_token': refresh_token.hex(),
        'refresh_token_expired': refresh_token_expired,
    }), 200


@app.route('/voicechange/api/token/refresh', methods=['POST'])
def __voicechange_api_token_refresh():

    # Get Refresh-Token
    refresh_token = request.json.get('refresh_token')
    if not refresh_token:
        return jsonify({'message': 'Invalid Token'}), 400
    refresh_token = bytes.fromhex(refresh_token)
    refresh_token_hash = hashlib.sha256(refresh_token).hexdigest()

    # Make Query
    token = session.query(Token)\
        .filter_by(refresh_token_hash=refresh_token_hash)\
        .first()

    # Get utc timestamp of now
    timestamp = datetime.now(timezone.utc)

    # Certification of Refresh-Token
    if any([
        not token,
        not token.refresh_token_expired
            .replace(tzinfo=timezone.utc) > timestamp
    ]):
        return jsonify({'message': 'Refresh-Token expired'}), 400

    # Redirect
    return __voicechange_api_token_fetch()


@app.route('/voicechange/api/token/destroy', methods=['POST'])
def __voicechange_api_token_destroy():

    # Get utc timestamp of now
    timestamp = datetime.now(timezone.utc)

    # Get Access-Token from json
    access_token = request.json.get('access_token')
    if not access_token:
        return jsonify({'message': 'Invalid Token'}), 400
    access_token = bytes.fromhex(access_token)
    access_token_hash = hashlib.sha256(access_token).hexdigest()

    # Get Refresh-Token from json
    refresh_token = request.json.get('refresh_token')
    if not refresh_token:
        return jsonify({'message': 'Invalid Token'}), 400
    refresh_token = bytes.fromhex(refresh_token)
    refresh_token_hash = hashlib.sha256(refresh_token).hexdigest()

    # Get Token
    token = session.query(Token)\
        .filter_by(access_token_hash=access_token_hash)\
        .filter_by(refresh_token_hash=refresh_token_hash)\
        .first()

    if any([
        not token,
        not token.refresh_token_expired
            .replace(tzinfo=timezone.utc) > timestamp
    ]):
        return jsonify({'message': 'Refresh-Token expired'}), 400

    # Delete Token
    session.delete(token)
    session.commit()
    return jsonify({}), 201


@app.route('/voicechange/api/audio/convert', methods=['POST'])
def __voicechange_api_audio_convert():

    # Get utc timestamp of now
    timestamp = datetime.now(timezone.utc)

    # Get Access-Token
    access_token = request.form.get('access_token')
    if not access_token:
        return jsonify({'message': 'Invalid Access-Token'}), 400
    access_token = bytes.fromhex(access_token)
    access_token_hash = hashlib.sha256(access_token).hexdigest()

    # Get Token
    user = session.query(Token)\
        .filter_by(access_token_hash=access_token_hash)\
        .first()

    # Verification of Access-Token
    if any([
        not user,
        not user.access_token_expired
            .replace(tzinfo=timezone.utc) > timestamp,
    ]):
        return jsonify({'message': 'Access-Token expired'}), 400

    # Get Target-Audio file
    audio = request.files.get('audio')
    if not audio:
        return jsonify({'message': 'Audio file not found'}), 400

    audios = AudioSegment.from_wav(audio)

    # Get JSON parameters
    params = json.loads(request.form.get('params', '{}'))
    pitch = params.get('pitch', 0)
    volume = params.get('volume', 0)
    speed = params.get('speed', 1.0)

    # Adjust pitch
    if pitch != 0:
        overrides = {'frame_rate': int(
            audios.frame_rate * (2 ** (pitch / 12.0)))}
        audios = audios._spawn(audios.raw_data, overrides=overrides)
        audios = audios.set_frame_rate(audios.frame_rate)

    # Adjust volume
    if volume != 0:
        audios = audios + volume

    # Adjust speed
    if speed != 1.0:
        overrides = {'frame_rate': int(audios.frame_rate * speed)}
        audios = audios._spawn(audios.raw_data, overrides=overrides)
        audios = audios.set_frame_rate(audios.frame_rate)

    # Save the result to a temporary file
    temp = uuid.uuid4()
    temp = pathlib.Path(f'./temp/{temp.hex}')
    while temp.exists():
        temp = uuid.uuid4()
        temp = pathlib.Path(f'./temp/{temp.hex}')
    temp.parent.mkdir(parents=True, exist_ok=True)

    # audio.export(temp_location, format='wav')
    audios.export(temp)

    # Create response
    response = send_file(
        temp,
        mimetype='audio/wav',
        as_attachment=True,
        download_name='converted_audio.wav',
    )

    # Return response
    return response, 200


if __name__ == '__main__':
    app.run(debug=True)
