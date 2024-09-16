
import streamlit as st
import os
from app import Session, User, ConversionHistory

def history_display():
    st.title('Conversion History')

    if 'user_id' not in st.session_state:
        st.error("Please log in to view your conversion history.")
        return

    user_id = st.session_state.user_id

    with Session() as session:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            st.error("User not found.")
            return

        conversions = session.query(ConversionHistory).filter_by(user_id=user_id).order_by(ConversionHistory.conversion_date.desc()).all()

        if not conversions:
            st.info("No conversion history found.")
            return

        # マークダウンテーブルのヘッダーを作成
        markdown_table = "| Original Filename | Converted Filename | Conversion Date |\n"
        markdown_table += "|-------------------|--------------------|-----------------|\n"

        # データを行として追加
        for conversion in conversions:
            markdown_table += f"| {conversion.original_filename} | {conversion.converted_filename} | {conversion.conversion_date.strftime('%Y-%m-%d %H:%M:%S')} |\n"

        # マークダウンテーブルを表示
        st.markdown(markdown_table)

        st.subheader("Download Converted File")
        
        # ファイル選択のためのセレクトボックスを作成（変換後のファイル名を使用）
        file_options = [conv.converted_filename for conv in conversions]
        selected_file = st.selectbox("Select a converted file to download:", file_options)

        if st.button("Download Selected File"):
            selected_conversion = next(conv for conv in conversions if conv.converted_filename == selected_file)
            try:
                file_path = os.path.join('audio', selected_conversion.converted_filename)
                if os.path.exists(file_path):
                    with open(file_path, "rb") as file:
                        file_content = file.read()
                        st.download_button(
                            label=f"Download {selected_conversion.original_filename}",
                            data=file_content,
                            file_name=selected_conversion.converted_filename,
                            mime="audio/wav",
                            key="download_file"
                        )
                else:
                    st.error(f"File not found: {selected_conversion.converted_filename}")
            except Exception as e:
                st.error(f"Error downloading file: {str(e)}")

if __name__ == "__main__":
    # This is for testing the history view independently
    st.session_state.user_id = 1  # Mock user ID for testing
    history_display()