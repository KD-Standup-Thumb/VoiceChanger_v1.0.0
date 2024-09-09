import streamlit as st
import hashlib
import sqlite3

# セッション状態の初期化
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# データベースの接続と操作
def get_db_connection():
    conn = sqlite3.connect('users.db')
    return conn

def create_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_user(username: str, password: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        return False  # ユーザー名が既に存在する場合
    finally:
        conn.close()
    return True

def get_user(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def home():
        # タイトルをカスタムサイズで表示し、中央に配置
    st.markdown(
        '''
        <style>
        .title {
            text-align: center;
            font-size: 5em;
            white-space: nowrap; /* テキストの改行を防ぐ */
            margin: 3;
        }
        </style>
        <div class="title">voice_changerへようこそ！</div>
        ''',
        unsafe_allow_html=True
    )

    # ボタンの配置
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.write("")  # 空のセルで余白を作成
    
    with col2:
        if st.button('アカウント作成', key='create_account'):
            st.session_state.page = 'create_account'
    
    with col3:
        if st.button('ログイン', key='login'):
            st.session_state.page = 'login'

    # voice_changerの概要説明コメント
    st.write("voice_changerではあなたの声、もしくは音声ファイルを別人の声に変換できます。")

def create_account():
    st.title('アカウント作成')
    username = st.text_input('ユーザー名')
    password = st.text_input('パスワード', type='password')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button('アカウント作成', key='create'):
            if username and password:
                if get_user(username):
                    st.error('このユーザー名は既に使用されています。')
                else:
                    if save_user(username, hash_password(password)):
                        st.success('アカウントが作成されました。')
                        st.session_state.page = 'home'
                    else:
                        st.error('アカウントの作成に失敗しました。')
            else:
                st.error('ユーザー名とパスワードを入力してください。')
    
    with col2:
        if st.button('ホームに戻る', key='back'):
            st.session_state.page = 'home'

def login():
    st.title('ログイン')
    username = st.text_input('ユーザー名')
    password = st.text_input('パスワード', type='password')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button('ログイン', key='login_submit'):
            user = get_user(username)
            if user and user[1] == hash_password(password):
                st.success('ログインに成功しました。')
            else:
                st.error('ユーザー名またはパスワードが正しくありません。')
    
    with col2:
        if st.button('ホームに戻る', key='home'):
            st.session_state.page = 'home'

# メイン関数
def main():
    create_db()  # アプリケーション起動時にデータベースを作成
    if st.session_state.page == 'home':
        home()
    elif st.session_state.page == 'create_account':
        create_account()
    elif st.session_state.page == 'login':
        login()

if __name__ == '__main__':
    main()
