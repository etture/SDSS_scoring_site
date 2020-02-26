import os
from flask import Flask, render_template, request
from werkzeug import secure_filename
import pandas as pd
from sklearn.metrics import log_loss
import pickle

app = Flask(__name__)

# 업로드 HTML 렌더링
@app.route('/upload')
def render_file():
    return render_template('upload.html')

# 파일 업로드 처리
@app.route('/fileUpload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        team = request.form.get('team')
        print('team: ', type(team))
        # 저장할 경로 + 파일명
        upload_directory = os.path.join(os.path.dirname(__file__), 'upload')
        file_abspath = os.path.join(
            upload_directory, secure_filename(file.filename))
        if not os.path.exists('upload'):
            os.makedirs('upload')
        file.save(file_abspath)

        # Get scores
        score = get_score(file_abspath)

        # Move files
        if not os.path.exists('previous'):
            os.makedirs('previous')
        base_file = os.path.basename(os.path.normpath(file_abspath))
        if os.path.exists(os.path.join('previous', base_file)):
            counter = 0
            while os.path.exists(os.path.join('previous', base_file)):
                counter += 1
                identifier, extension = base_file.split('.')
                identifier += f'_{counter}'
                base_file = '.'.join([identifier, extension])
        new_path = os.path.join(os.path.dirname(os.path.dirname(file_abspath)), 'previous', base_file)
        os.rename(file_abspath, new_path)

        if not os.path.exists('scores.pickle'):
            with open('scores.pickle', 'wb') as f:
                base_data = {
                    1: {'score': 35, 'file': ''}, 
                    2: {'score': 35, 'file': ''}, 
                    3: {'score': 35, 'file': ''}
                }
                pickle.dump(base_data, f)

        with open('scores.pickle', 'rb') as f:
            data = pickle.load(f)
        
        if score < data[int(team)]['score']:
            data[int(team)]['score'] = score
            data[int(team)]['file'] = new_path

        with open('scores.pickle', 'wb') as f:
            pickle.dump(data, f)

        return f'''<h3>{team}팀 파일 업로드 성공!</h3>
                <h4>파일명: {secure_filename(file.filename)}</h4>
                <h4>점수: {score}</h4>'''


@app.route('/getLeaderboard_abcdefg', methods=['GET', 'POST'])
def get_leaderboard():
    if not os.path.exists('scores.pickle'):
        return 'no leaderboard created'
    with open('scores.pickle', 'rb') as f:
        data = pickle.load(f)
    show_str = ''
    for k, v in data.items():
        show_str += f'<h3>{k}팀: {"NA" if v["score"] == 35 else v["score"]}</h3>'
    return show_str


rename_dict = {'STAR_WHITE_DWARF': 0, 'STAR_CATY_VAR': 1, 'STAR_BROWN_DWARF': 2,
               'SERENDIPITY_RED': 3, 'REDDEN_STD': 4, 'STAR_BHB': 5, 'GALAXY': 6,
               'SERENDIPITY_DISTANT': 7, 'QSO': 8, 'SKY': 9, 'STAR_RED_DWARF': 10, 'ROSAT_D': 11,
               'STAR_PN': 12, 'SERENDIPITY_FIRST': 13, 'STAR_CARBON': 14, 'SPECTROPHOTO_STD': 15,
               'STAR_SUB_DWARF': 16, 'SERENDIPITY_MANUAL': 17, 'SERENDIPITY_BLUE': 18}


def get_ground_truth(filename):
    pickle_in = open(filename, "rb")
    validate = pickle.load(pickle_in)
    validate2 = list()
    for v in validate:
        validate2.append(rename_dict[v])
    return validate2


def get_submission_file(filename):
    sub = pd.read_csv(filename)
    renamed = sub.rename(columns=rename_dict)
    return renamed


def get_score(sub_file, ground_truth_filename='./ybigta_validate_full.pickle'):
    ground_truth = get_ground_truth(ground_truth_filename)
    submission = get_submission_file(sub_file)
    return log_loss(ground_truth, submission[submission.columns[1:]].values)


if __name__ == '__main__':
    # 서버 실행
    app.run(debug=True, host='0.0.0.0')
