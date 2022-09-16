import os
import gspread
import csv
import io

# Google spreadsheet用
credentials = {
    "type": os.environ.get("service_account_key_type"),
    "project_id": os.environ.get("service_account_key_project_id"),
    "private_key_id": os.environ.get("service_account_key_private_key_id"),
    "private_key": os.environ.get("service_account_key_private_key").replace(
        "\\n", "\n"
    ),
    "client_email": os.environ.get("service_account_key_client_email"),
    "client_id": os.environ.get("service_account_key_client_id"),
    "auth_uri": os.environ.get("service_account_key_auth_uri"),
    "token_uri": os.environ.get("service_account_key_token_uri"),
    "auth_provider_x509_cert_url": os.environ.get(
        "service_account_key_auth_provider_x509_cert_url"
    ),
    "client_x509_cert_url": os.environ.get("service_account_key_client_x509_cert_url"),
}

false_words = ["N", "NO", "F", "FALSE", "OFF", "0"]


def load_url(sheet_url=""):

    # Googleアカウント認証
    gc = gspread.service_account_from_dict(credentials)

    # ワークシートを開く
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.sheet1

    # タイトル取得
    title = sh.title

    # データ読み込み
    data = [
        value
        for value in worksheet.get_all_values()
        if value and value[0] and value[0][0] != "#"
    ]
    [common_question, *_], *questions = data
    if common_question in false_words:
        common_question = "正解を入力してください。"
    questions = [question[:2] for question in questions if len(question) >= 2]
    return title, common_question, questions


def load_csv_file(csv_file=None):
    title = ".".join(csv_file.name.split(".")[:-1])
    reader = csv.reader(io.StringIO(csv_file.getvalue().decode("utf-8")))
    data = [value for value in reader if value and value[0] and value[0][0] != "#"]
    [common_question, *_], *questions = data
    if common_question in false_words:
        common_question = "正解を入力してください。"
    questions = [question[:2] for question in questions if len(question) >= 2]
    return title, common_question, questions


def load_csv_text(csv_text="", csv_title=""):
    title = str(csv_title)
    reader = csv.reader(csv_text.splitlines())
    data = [value for value in reader if value and value[0] and value[0][0] != "#"]
    [common_question, *_], *questions = data
    if common_question in false_words:
        common_question = "正解を入力してください。"
    questions = [question[:2] for question in questions if len(question) >= 2]
    return title, common_question, questions
