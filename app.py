import streamlit as st
import pandas as pd
import hashlib

# セッション状態の初期化
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# ユーザーデータの読み込み（または作成）
try:
    users_df = pd.read_csv('users.csv')
except FileNotFoundError:
    users_df = pd.DataFrame(columns=['username', 'password'])

def save_users():
    users_df.to_csv('users.csv', index=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def home():
    st.title('voice_changerへようこそ！')

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

def create_account():
    st.title('アカウント作成')
    username = st.text_input('ユーザー名')
    password = st.text_input('パスワード', type='password')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button('アカウント作成', key='create'):
            if username and password:
                if username in users_df['username'].values:
                    st.error('このユーザー名は既に使用されています。')
                else:
                    users_df.loc[len(users_df)] = [username, hash_password(password)]
                    save_users()
                    st.success('アカウントが作成されました。')
                    st.session_state.page = 'home'
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
            user = users_df[users_df['username'] == username]
            if not user.empty and user['password'].values[0] == hash_password(password):
                st.success('ログインに成功しました。')
            else:
                st.error('ユーザー名またはパスワードが正しくありません。')
    
    with col2:
        if st.button('ホームに戻る', key='home'):
            st.session_state.page = 'home'

# メイン関数
def main():
    if st.session_state.page == 'home':
        home()
    elif st.session_state.page == 'create_account':
        create_account()
    elif st.session_state.page == 'login':
        login()

if __name__ == '__main__':
    main()


# test