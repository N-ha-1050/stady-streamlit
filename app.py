import streamlit as st
from main import load_id, load_csv_file, load_csv_text, get_id_from_url, write_record
import random

options = ["Googleスプレッドシートを共有", "csvファイルをアップロード", "csv形式で入力", "現在のデータを表示・ダウンロード"]
table = [
    ["共通の問題文", ""],
    ["#コメント行", ""],
    ["問1の問題", "問1の答え"],
    ["問2の問題", "問2の答え"],
    ["問3の問題", "問3の答え"],
    ["…", "…"],
    ["問nの問題", "問nの答え"],
]


def init_session_state(common_question, questions, title, opt, is_record=False):
    st.session_state["common_question"] = common_question
    st.session_state["questions"] = questions
    st.session_state["title"] = title
    st.session_state["opt"] = opt
    st.session_state["is_record"] = is_record


def change_url():
    try:
        id = get_id_from_url(st.session_state.sheet_url)
    except:
        st.sidebar.error("接続に失敗しました。")
        return 0
    st.session_state["sheet_id"] = id
    change_id()


def change_id(is_record=False):
    try:
        title, common_question, questions, is_record = load_id(
            st.session_state.sheet_id, is_record
        )
    except:
        st.sidebar.error(f"接続に失敗しました。")
        return 0
    if not questions:
        return 0
    if is_record:
        st.info("この問題では解答データを記録します。データ書き込みのため速度が低下する場合があります。停止するには画面下のボタンを押してください。")
    init_session_state(common_question, questions, title, options[0], is_record)
    give()


def change_file():
    if st.session_state.csv_file is None:
        return 0
    try:
        title, common_question, questions = load_csv_file(st.session_state.csv_file)
    except:
        st.sidebar.error("読み込みに失敗しました。")
        return 0
    if not questions:
        return 0
    init_session_state(common_question, questions, title, options[1])
    give()


def change_text():
    if st.session_state.csv_text is None:
        return 0
    try:
        title, common_question, questions = load_csv_text(
            st.session_state.csv_text, st.session_state.csv_text_title
        )
    except:
        st.sidebar.error("読み込みに失敗しました。")
        return 0
    if not questions:
        return 0
    init_session_state(common_question, questions, title, options[2])
    give()


def stop_record():
    st.session_state["is_record"] = False
    give()


def give(next=True):
    if next or "q" not in st.session_state or "a" not in st.session_state:
        q, a = random.choice(st.session_state["questions"])
        st.session_state["q"] = q
        st.session_state["a"] = a

    st.title(st.session_state["title"])
    if "msg" in st.session_state and st.session_state["msg"]:
        st.info(st.session_state["msg"])
    st.markdown(st.session_state["q"])
    st.text_input(st.session_state["common_question"], key="answer", on_change=check)
    if st.session_state.is_record:
        st.button("記録を停止", on_click=stop_record)


def check():
    if st.session_state.answer == st.session_state["a"]:
        st.session_state["msg"] = "正解"
    else:
        st.session_state[
            "msg"
        ] = f'不正解 正解: {st.session_state["a"]} 誤答: {st.session_state.answer}'
    if st.session_state["is_record"]:
        try:
            is_write, msg = write_record(
                st.session_state.sheet_id,
                st.session_state.q,
                st.session_state.a,
                st.session_state.answer,
            )
        except:
            st.info("記録に失敗しました。")
        else:
            if msg:
                if is_write:
                    st.info(msg)
                else:
                    st.error(msg)
    st.session_state.answer = ""
    give()


def click_button(data):
    st.session_state.csv_text = data
    st.session_state.csv_text_title = st.session_state["title"]
    st.session_state.opt = options[2]
    give(False)


st.sidebar.title("Stady")

params = st.experimental_get_query_params()
if "sheet_url" in params.keys() and "title" not in st.session_state:
    st.session_state["sheet_url"] = params["sheet_url"][0]
    change_url()
if "sheet_id" in params.keys() and "title" not in st.session_state:
    st.session_state["sheet_id"] = params["sheet_id"][0]
    change_id()
if "id" in params.keys() and "title" not in st.session_state:
    st.session_state["sheet_id"] = params["id"][0]
    change_id(is_record=True)


st.sidebar.selectbox(
    "問題の読み込み・表示方法を選択してください。",
    options=(options if "title" in st.session_state else options[:3]),
    key="opt",
    on_change=(give if "title" in st.session_state else lambda x: 0),
    args=(False,),
)
st.sidebar.caption("選択を変更すると編集中のデータは失われます。")
num = options.index(st.session_state.opt)
if 0 <= num <= 2:
    st.sidebar.subheader("問題の読み込み")
if num == 0:
    st.sidebar.text_input(
        "以下の形式のGoogleスプレッドシートを「リンクを知っている全員」が「閲覧者」になるように共有し、リンクを入力してください。",
        key="sheet_url",
        placeholder="https://docs.google.com/spreadsheet/ccc?key=0Bm...FE&hl",
        on_change=change_url,
    )
elif num == 1:
    st.sidebar.file_uploader(
        "以下の形式のcsvファイルをアップロードしてください。", key="csv_file", type="csv", on_change=change_file
    )
elif num == 2:
    with st.sidebar.form("csv_text_form"):
        st.text_input("タイトル", key="csv_text_title")
        st.text_area("以下の形式で入力してください。", key="csv_text")
        submitted = st.form_submit_button("送信", on_click=change_text)
elif num == 3:
    data = [[st.session_state["common_question"]], *st.session_state["questions"]]
    st.sidebar.download_button(
        "csv形式でダウンロード",
        data="\n".join([",".join(value) for value in data]),
        file_name=f'{st.session_state["title"]}.csv',
        mime="text/csv",
    )
    st.sidebar.caption("アプリで整形後のデータです。")
    st.sidebar.write(f'タイトル：{st.session_state["title"]}')
    st.sidebar.table(
        data=[[st.session_state["common_question"], ""], *st.session_state["questions"]]
    )
    st.sidebar.button(
        "テキストエリアに反映",
        on_click=click_button,
        args=("\n".join([",".join(value) for value in data]),),
    )

if 0 <= num <= 2:
    st.sidebar.subheader("対応ファイル形式")
    st.sidebar.table(data=table)
    st.sidebar.markdown("各問題の問題文にはMarkdownを使えます。")
if "title" not in st.session_state:
    st.write("サイドバーから問題の読み込みをしてください。")
