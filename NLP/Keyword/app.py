# coding: utf-8


from flask import Flask, request, url_for, redirect, render_template, abort,\
        flash
import json
import requests
import  xml.etree.ElementTree as ET
from jieba import analyse

# configuration
DEBUG = False
L_USERNAME = 'your api username'
L_PASSWORD = 'your api password'

app = Flask(__name__)
app.config.from_pyfile('config.py')
#app.config.from_object(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = int(request.form['username'])
        return  redirect(url_for('home', username=username))
    return render_template('index.html')


@app.route('/user/<username>')
def home(username):
    return render_template('home.html', username=username)


@app.route('/static/treemap/<username>.json')
def treemap(username, most_common=50):
    """Generate json data needed by treemap for d3.js."""

    kw_str = generate_data(username)
    #jieba.load_userdict(app.config['USERDICT'])
    kw = analyse.extract_tags(kw_str, most_common)
    #颠倒位置, 使name作为key, size作为value, dict()处理时就不会覆盖具有
    #相同权重的值了.
    #TODO 剔除数字
    kw = dict([tuple(reversed(i)) for i in kw])
    j = json.dumps({"name": "kw",
                    "children": [{"name": key, "size": value} for key, value\
                     in kw.items()]}, indent=2)
    return j

        
def parse_history(username, l_user=app.config['L_USERNAME'],
        l_pass=app.config['L_PASSWORD']):
    """Return XML root """
    
    base_url = 'http://opac.gdufs.edu.cn:8991/X?op=loan_history&bor_id=G%s&bor_id_type=00\
                &user_name=%s&user_password=%s'
    url = base_url % (username, l_user, l_pass)
    res = requests.get(url, stream=True)
    root = ET.parse(res.raw).getroot()
    if root[0].text.find('ID') != -1:
        username = username[4:]
        url = base_url % (username, l_user, l_pass)
        res = requests.get(url, stream=True)
        root = ET.parse(res.raw).getroot()
    return root


def generate_data(username):
    """Generate data for table record and book """

    root = parse_history(username=str(username))
    total = int(root[1].text)
    # 图书馆那边最多显示500条记录
    if total > 500:
        total = 500
    title_all = []
    for i in xrange(3, 3 + total):
        if not  root[i].find('z13-title').text:
            continue
        else:
            title = root[i].find('z13-title').text
            title_all.append(title)
    return ','.join(title_all)


if __name__ == '__main__':
    app.run('0.0.0.0')
