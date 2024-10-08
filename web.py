import streamlit as st
import hashlib
import json
import requests
import os
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

# Database setup
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    settings = relationship("UserSetting", back_populates="user")
    api_key = relationship("APIKey", back_populates="user", uselist=False)
    conversions = relationship("ConversionHistory", back_populates="user")


class UserSetting(Base):
    __tablename__ = 'user_settings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    pitch = Column(String, nullable=False)
    volume = Column(String, nullable=False)
    speed = Column(String, nullable=False)
    user = relationship("User", back_populates="settings")


class APIKey(Base):
    __tablename__ = 'api_keys'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    api_key = Column(String, nullable=False)
    user = relationship("User", back_populates="api_key")


class ConversionHistory(Base):
    __tablename__ = 'conversion_history'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    original_filename = Column(String, nullable=False)
    converted_filename = Column(String, nullable=False)
    conversion_date = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="conversions")


engine = create_engine('sqlite:///voice_changer.db', echo=True)
Session = scoped_session(sessionmaker(bind=engine))
Base.metadata.create_all(engine)

# Utility functions
__WEBAPI_URL = 'http://127.0.0.1:5000/voicechange/api'


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def __webapi_token_create():
    __URL = f'{__WEBAPI_URL}/token/create'
    try:
        response = requests.post(__URL, timeout=5)
        if response.status_code == 200:
            return response.json().get('access_token')
    except requests.RequestException as e:
        st.error(f"API key generation failed: {str(e)}")
    return None


def save_setting(user_id, setting_name, setting_value):
    with Session() as session:
        setting = session.query(UserSetting).filter_by(
            user_id=user_id, setting_name=setting_name).first()
        if setting:
            setting.setting_value = setting_value
        else:
            new_setting = UserSetting(
                user_id=user_id,
                setting_name=setting_name,
                setting_value=setting_value
            )
            session.add(new_setting)
        session.commit()


def __webapi_audio_convert(file_path, api_key, params):
    api_url = "http://127.0.0.1:5000/voicechange/api/audio/convert"
    files = {'audio': open(file_path, 'rb')}
    data = {
        'access_token': api_key,
        'params': json.dumps(params)
    }
    try:
        response = requests.post(api_url, files=files, data=data)

        print(response)
        if response.status_code == 200:
            return response.content
        st.error(f"Server error occurred. Status code: {response.status_code}")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    return None


def save_conversion_history(user_id, original_filename, converted_filename):
    with Session() as session:
        new_conversion = ConversionHistory(
            user_id=user_id,
            original_filename=original_filename,
            converted_filename=converted_filename
        )
        session.add(new_conversion)
        session.commit()

# View functions


def __view_home():
    st.title("Welcome to Voice Changer!")
    col1, col2 = st.columns(2)

    # Create Account ボタンが押されたかどうかを session_state で管理
    if col1.button('Create Account'):
        st.session_state.page = 'create_account'

    # Login ボタンが押されたかどうかを session_state で管理
    if col2.button('Login'):
        st.session_state.page = 'login'

    st.write(
        "Voice Changer allows you to transform your"
        "voice or audio files into different voices."
    )


def __view_signin():
    st.title('Create Account')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    # Create Account ボタンの処理を session_state で管理
    if st.button('Create Account'):
        if not (username and password):
            st.error('Please enter both username and password.')
            return

        with Session() as session:
            if session.query(User).filter_by(username=username).first():
                st.error('Username already exists.')
                return

            new_user = User(username=username,
                            password=hash_password(password))
            session.add(new_user)
            session.flush()
            api_key = __webapi_token_create()
            if not api_key:
                session.rollback()
                st.error(
                    'Failed to create account. Could not generate API key.')
                return

            new_api_key = APIKey(user_id=new_user.id, api_key=api_key)
            session.add(new_api_key)
            session.commit()
            st.success('Account created successfully.')
            st.session_state.page = 'login'  # ログインページへ移動


def __view_login():
    st.title('Login')
    username = st.text_input('Username')
    password = st.text_input('Password', type='password')

    # Login ボタンの処理を session_state で管理
    if st.button('Login'):
        with Session() as session:
            user = session.query(User).filter_by(username=username).first()
            if user and user.password == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.user_id = user.id
                st.session_state.page = 'main'  # メインページへ移動
            else:
                st.error('Invalid username or password.')


def __view_main():

    with Session() as session:
        user = session.query(User)\
            .filter_by(id=st.session_state.user_id)\
            .first()
        api_key = user.api_key

    st.title('Voice Changer Main')

    params = {}

    columnL, columnR = st.columns(2)

    with columnL:
        st.subheader("Voice Settings")
        params['pitch'] = st.slider("pitch adjustment", 0.0, 2.0, 1.0)
        params['volume'] = st.slider("volume adjustment", 0.0, 2.0, 1.0)
        params['speed'] = st.slider("speed adjustment", 0.0, 2.0, 1.0)

    with columnR:
        st.subheader("File Upload")
        uploaded_file = st.file_uploader("Upload WAV file", type=["wav"])
        if not uploaded_file:
            return

        st.audio(uploaded_file, format='audio/wav')
        if not st.button("Process Audio"):
            return

        if not api_key:
            st.error(
                "No valid API key found. Please contact the administrator.")
            return

        save_dir = "./audio"
        os.makedirs(save_dir, exist_ok=True)
        original_filename = uploaded_file.name
        file_path = os.path.join(save_dir, f"{uuid.uuid4()}.wav")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        processed_audio = __webapi_audio_convert(
            file_path, api_key.api_key, params)
        if processed_audio:
            st.success("Audio conversion completed!")
            st.audio(processed_audio, format='audio/wav')

            # 変換後のファイル名を生成
            unique_filename = f"{uuid.uuid4()}_converted_{original_filename}"
            converted_file_path = os.path.join(save_dir, unique_filename)

            # 変換された音声ファイルを保存
            with open(converted_file_path, "wb") as f:
                f.write(processed_audio)

            # 履歴に保存
            save_conversion_history(
                st.session_state.user_id, original_filename, unique_filename)

            st.download_button("Download converted audio",
                               processed_audio, unique_filename, "audio/wav")

# Main application


def main():
    st.set_page_config(page_title="Voice Changer", layout="wide")

    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # サイドバー
    st.sidebar.title("Voice Changer")
    if st.session_state.logged_in:
        if st.sidebar.button('Logout'):
            st.session_state.logged_in = False
            st.session_state.page = 'home'
        view = st.sidebar.radio("Navigation", ["Main", "History"])
        st.session_state.page = view.lower()

    # メインコンテンツ
    if st.session_state.page == 'home':
        __view_home()
    elif st.session_state.page == 'login':
        __view_login()
    elif st.session_state.page == 'create_account':
        __view_signin()
    elif st.session_state.logged_in:
        if st.session_state.page == 'main':
            __view_main()
        elif st.session_state.page == 'history':
            from conversion_history import history_display
            history_display()
    else:
        st.session_state.page = 'home'


if __name__ == '__main__':
    main()
