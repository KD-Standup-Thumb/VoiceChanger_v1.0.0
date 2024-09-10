import streamlit as st
import hashlib
import sqlite3

# セッション状態の初期化
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'main'

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
    st.markdown(
        '''
        <style>
        .title {
            text-align: center;
            font-size: 5em;
            white-space: nowrap;
            margin: 3;
        }
        </style>
        <div class="title">voice_changerへようこそ！</div>
        ''',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.write("")
    
    with col2:
        if st.button('アカウント作成', key='create_account'):
            st.session_state.page = 'create_account'
    
    with col3:
        if st.button('ログイン', key='login'):
            st.session_state.page = 'login'

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
                st.session_state.logged_in = True
                st.session_state.page = 'main'
            else:
                st.error('ユーザー名またはパスワードが正しくありません。')
    
    with col2:
        if st.button('ホームに戻る', key='home'):
            st.session_state.page = 'home'

# Voice Changer の機能
def change_pitch():
    st.write("音高変更機能はここに実装します。")

def change_timbre():
    st.write("音色変更機能はここに実装します。")

def save_config():
    st.write("設定保存機能はここに実装します。")

def edit_config():
    st.write("設定編集機能はここに実装します。")

def select_config():
    st.write("設定選択機能はここに実装します。")

def save_timbre():
    st.write("音色保存機能はここに実装します。")

def save_pitch():
    st.write("音高保存機能はここに実装します。")

def save_pitch_interval():
    st.write("音程保存機能はここに実装します。")

# 履歴関連の機能
def save_history():
    st.write("音声変換履歴保存機能はここに実装します。")

def search_history():
    st.write("音声変換履歴検索機能はここに実装します。")

def delete_history():
    st.write("音声変換履歴削除機能はここに実装します。")

def main_view():
    st.title('Voice Changer メイン画面')
    
    # 機能選択
    feature = st.selectbox(
        "機能を選択してください",
        ("音高変更", "音色変更", "設定保存", "設定編集", "設定選択", "音色保存", "音高保存", "音程保存")
    )
    
    # 選択された機能を表示
    if feature == "音高変更":
        change_pitch()
    elif feature == "音色変更":
        change_timbre()
    elif feature == "設定保存":
        save_config()
    elif feature == "設定編集":
        edit_config()
    elif feature == "設定選択":
        select_config()
    elif feature == "音色保存":
        save_timbre()
    elif feature == "音高保存":
        save_pitch()
    elif feature == "音程保存":
        save_pitch_interval()

def history_view():
    st.title('音声変換履歴')
    
    # 履歴機能選択
    history_feature = st.selectbox(
        "履歴機能を選択してください",
        ("履歴保存", "履歴検索", "履歴削除")
    )
    
    # 選択された履歴機能を表示
    if history_feature == "履歴保存":
        save_history()
    elif history_feature == "履歴検索":
        search_history()
    elif history_feature == "履歴削除":
        delete_history()

def main_screen():
    # サイドバーにメニューを追加
    st.sidebar.title("メニュー")
    view = st.sidebar.radio("画面選択", ("メイン画面", "音声変換履歴"))
    
    if view == "メイン画面":
        st.session_state.current_view = 'main'
    else:
        st.session_state.current_view = 'history'
    
    # 選択されたビューを表示
    if st.session_state.current_view == 'main':
        main_view()
    else:
        history_view()
    
    if st.sidebar.button('ログアウト'):
        st.session_state.logged_in = False
        st.session_state.page = 'home'
        st.experimental_rerun()

# メイン関数
def main():
    create_db()  # アプリケーション起動時にデータベースを作成
    if st.session_state.page == 'home':
        home()
    elif st.session_state.page == 'create_account':
        create_account()
    elif st.session_state.page == 'login':
        login()
    elif st.session_state.page == 'main' and st.session_state.logged_in:
        main_screen()
    else:
        st.session_state.page = 'home'
        st.experimental_rerun()

if __name__ == '__main__':
    main()