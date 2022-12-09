import os
import gspread
import csv
import io
import random

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

record_sheet_id = os.environ.get("record_sheet_id")
rand_rate = int(os.environ.get("rand_rate"))

# Googleアカウント認証
gc = gspread.service_account_from_dict(credentials)
record_sh = gc.open_by_key(record_sheet_id)


def get_id_from_url(sheet_url=""):

    # Googleアカウント認証
    # gc = gspread.service_account_from_dict(credentials)

    # ワークシートを開く
    sh = gc.open_by_url(sheet_url)

    # id取得
    id = sh.id

    return id


def load_id(sheet_id="", is_record=False):

    # Googleアカウント認証
    # gc = gspread.service_account_from_dict(credentials)

    # ワークシートを開く
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.sheet1

    # タイトル取得
    title = sh.title

    # データ読み込み
    data = [
        value
        for value in worksheet.get_all_values()
        if value and value[0] and value[0][0] != "#"
    ]
    [common_question, is_record_text, *_], *questions = data
    if common_question in false_words:
        common_question = "正解を入力してください。"
    if is_record and (not is_record_text or is_record_text in false_words):
        is_record = False
    questions = [question[:2] for question in questions if len(question) >= 2]
    return title, common_question, questions, is_record


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


def write_record(sheet_id, q, a, answer):

    # rand_rate 分の一の割合で記録
    if random.randrange(rand_rate):
        return False, ""

    # シート一覧
    worksheet_titles = {worksheet.title for worksheet in record_sh.worksheets()}
    worksheet = None

    # ワークシートをロード
    title, common_question, questions, is_record = load_id(sheet_id, True)
    msg = ""

    # 記録禁止設定のとき
    if not is_record:
        return False, "記録が出来ません。"

    # 初期でないとき
    if sheet_id in worksheet_titles:
        worksheet = record_sh.worksheet(sheet_id)
        if worksheet.cell(1, 1).value != title:
            # if worksheet.get('A1') != title:
            worksheet.update_cell(1, 1, title)
            msg = "問題情報を更新しました。"
        if worksheet.cell(1, 2).value != common_question:
            # if worksheet.get('B1') != common_question:
            worksheet.update_cell(1, 2, common_question)
            msg = "問題情報を更新しました。"
        _, _, *sheet_questions = worksheet.get_all_values()

    # 初期設定
    else:
        worksheet = record_sh.add_worksheet(sheet_id, 0, 0)
        data = [[title, common_question], ["問題", "正答", "出題回数", "正解回数", "誤答"]]
        data += [[question, answer, 0, 0] for question, answer in questions]
        worksheet.append_rows(data)
        sheet_questions = [[question, answer, 0, 0] for question, answer in questions]
        msg = "記録データを新規作成しました。"

    # 記録の取得
    # questions: dict = {問題: (行番号, 正答, 出題回数, 正解回数, 誤答個数)}
    questions = {
        question: (
            i,
            answer,
            int(all_count),
            int(correct_count),
            len([True for wrong_answer in wrong_answers if wrong_answer]),
        )
        for i, (
            question,
            answer,
            all_count,
            correct_count,
            *wrong_answers,
        ) in enumerate(sheet_questions, 3)
    }
    if q in questions:
        i, answer_, all_count, correct_count, wrong_ansers_count = questions[q]
        if a != answer_:
            record_sh.del_worksheet(worksheet)
            return False, "データが破損していたので削除しました。"
        worksheet.update_cell(i, 3, all_count + 1)
        if a == answer:
            worksheet.update_cell(i, 4, correct_count + 1)
        else:
            worksheet.update_cell(i, wrong_ansers_count + 5, answer)
    else:
        record_sh.del_worksheet(worksheet)
        return False, "データが破損していたので削除しました。"
    return True, msg
