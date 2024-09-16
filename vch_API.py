import secrets
import hashlib
import pathlib
import uuid
# from pydub import AudioSegment
from flask import Flask, request, jsonify, send_file
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# Database setup
DATABASE_URL = 'sqlite:///vchapi.db'
engine = create_engine(DATABASE_URL)
Base = declarative_base()


class User(Base):
    __tablename__ = 'tokens'
    access_token_expired = Column(DateTime(timezone=True), nullable=False)
    access_token_hash = Column(String(64), nullable=False, primary_key=True)
    refresh_token_expired = Column(DateTime(timezone=True), nullable=False)
    refresh_token_hash = Column(String(64), nullable=False, unique=True)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
app = Flask(__name__)


@app.route('/voicechange/api/token/create', methods=['POST'])
def __voicechange_api_token_create():

    # Get utc timestamp of now
    timestamp = datetime.now(timezone.utc)

    # Generate new Access-Token
    access_token_expired = timestamp + timedelta(minutes=30)
    access_token = secrets.token_bytes(32)
    access_token_hash = hashlib.sha256(access_token).hexdigest()

    # Make Query
    query = session.query(User)\
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
    query = session.query(User)\
        .filter_by(refresh_token_hash=refresh_token_hash)

    # Verification Refresh-Token
    while query.first():
        refresh_token = secrets.token_bytes(32)
        refresh_token_hash = hashlib.sha256(refresh_token).hexdigest()

    # Add token to table
    user = User(
        access_token_expired=access_token_expired,
        access_token_hash=access_token_hash,
        refresh_token_expired=refresh_token_expired,
        refresh_token_hash=refresh_token_hash,
    )
    session.add(user)
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
        return jsonify({'message': 'Invalid Refresh-Token'}), 400
    refresh_token = bytes.fromhex(refresh_token)
    refresh_token_hash = hashlib.sha256(refresh_token).hexdigest()

    # Make Query
    user = session.query(User)\
        .filter_by(refresh_token_hash=refresh_token_hash)\
        .first()

    # Get utc timestamp of now
    timestamp = datetime.now(timezone.utc)

    # Certification of Refresh-Token
    if any([
        not user,
        not user.refresh_token_expired.replace(
            tzinfo=timezone.utc) > timestamp
    ]):
        return jsonify({'message': 'Refresh-Token expired'}), 400

    # Redirect
    return __voicechange_api_token_create()


@app.route('/voicechange/api/token/destroy', methods=['POST'])
def __voicechange_api_token_destroy():

    # Get utc timestamp of now
    timestamp = datetime.now(timezone.utc)

    # Get Access-Token from json
    access_token = request.json.get('access_token')
    if not access_token:
        return jsonify({'message': 'Invalid Access-Token'}), 400
    access_token = bytes.fromhex(access_token)
    access_token_hash = hashlib.sha256(access_token).hexdigest()

    # Get Refresh-Token from json
    refresh_token = request.json.get('refresh_token')
    if not refresh_token:
        return jsonify({'message': 'Invalid Refresh-Token'}), 400
    refresh_token = bytes.fromhex(refresh_token)
    refresh_token_hash = hashlib.sha256(refresh_token).hexdigest()

    # Get Token
    user = session.query(User)\
        .filter_by(access_token_hash=access_token_hash)\
        .filter_by(refresh_token_hash=refresh_token_hash)\
        .first()

    if any([
        not user,
        not user.refresh_token_expired.replace(
            tzinfo=timezone.utc) > timestamp
    ]):
        return jsonify({'message': 'Refresh-Token expired'}), 400

    # Delete Token
    session.delete(user)
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
    token = session.query(User)\
        .filter_by(access_token_hash=access_token_hash)\
        .first()

    # Verification of Access-Token
    if any([
        not token,
        not token.access_token_expired.replace(
            tzinfo=timezone.utc) > timestamp,
    ]):
        return jsonify({'message': 'Access-Token expired'}), 400

    # Get Target-Audio file
    audio = request.files.get('audio.wav')
    if not audio:
        return jsonify({'message': 'Audio file not found'}), 400
    """

    # Load audio file
    audio = AudioSegment.from_wav(target_audio)

    # Get JSON parameters
    params = request.json
    pitch = params.get('pitch', 0)
    volume = params.get('volume', 0)
    speed = params.get('speed', 1.0)

    # Adjust pitch
    if pitch != 0:
        audio = audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * (2 ** (pitch / 12.0)))
        })
        audio = audio.set_frame_rate(audio.frame_rate)

    # Adjust volume
    if volume != 0:
        audio = audio + volume

    # Adjust speed
    if speed != 1.0:
        audio = audio._spawn(audio.raw_data, overrides={
            "frame_rate": int(audio.frame_rate * speed)
        })
        audio = audio.set_frame_rate(audio.frame_rate)"""

    # Save the result to a temporary file
    temp = uuid.uuid4()
    temp = pathlib.Path(f'./temp/{temp.hex}')
    while temp.exists():
        temp = uuid.uuid4()
        temp = pathlib.Path(f'./temp/{temp.hex}')
    temp.parent.mkdir(parents=True, exist_ok=True)

    # audio.export(temp_location, format='wav')
    result_audio = audio
    result_audio.save(temp)

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
