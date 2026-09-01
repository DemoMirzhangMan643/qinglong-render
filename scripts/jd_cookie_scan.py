# -*- coding: utf-8 -*-
# cron: 0 0 31 2 *
# new Env('京东扫码获取Cookie');
"""
京东扫码获取 Cookie（面板专用增强版）

使用方法：
1. 在青龙【定时任务】中手动运行本任务
2. 日志中会输出二维码图片链接，浏览器打开该链接
3. 用京东 App 扫码并确认登录
4. 扫码成功后，Cookie 会自动写入青龙【环境变量】JD_COOKIE
   （已有相同账号则自动更新，多账号自动新增，无需手动填写）

基于 Zy143L/jd_cookie (jd_ck.py) 修改增强
"""
import json
import os
import sys
import time

import requests

requests.packages.urllib3.disable_warnings()

jd_ua = 'jdapp;android;10.0.5;11;0393465333165363-5333430323261366;network/wifi;model/M2102K1C;osVer/30;appBuild/88681;partner/lc001;eufv/1;jdSupportDarkMode/0;Mozilla/5.0 (Linux; Android 11; M2102K1C Build/RKQ1.201112.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.120 MQQBrowser/6.2 TBS/045534 Mobile Safari/537.36'

QL_PORT = os.environ.get('QL_PORT', '5700')
ql_url = 'http://127.0.0.1:{0}/'.format(QL_PORT)


def ql_get_token():
    """读取容器内 auth.json 获取面板 Token（同 wskey.py 方式）"""
    path = '/ql/data/config/auth.json'
    if not os.path.isfile(path):
        path = '/ql/config/auth.json'
    if not os.path.isfile(path):
        print('未找到青龙 auth.json，请在青龙面板内运行本脚本')
        sys.exit(1)
    with open(path, 'r') as f:
        auth = json.load(f)
    token = auth.get('token', '')
    if token:
        try:
            r = requests.get(ql_url + 'api/user',
                             headers={'Authorization': 'Bearer {0}'.format(token)}, timeout=10)
            if r.status_code == 200:
                return token
        except Exception:
            pass
    r = requests.post(ql_url + 'api/user/login',
                      json={'username': auth['username'], 'password': auth['password']},
                      timeout=10)
    return r.json()['data']['token']


def ql_save_cookie(ck, pin):
    """将 Cookie 写入青龙环境变量 JD_COOKIE（同账号更新，新账号新增）"""
    token = ql_get_token()
    headers = {'Authorization': 'Bearer {0}'.format(token), 'Content-Type': 'application/json'}
    r = requests.get(ql_url + 'api/envs?searchValue=JD_COOKIE', headers=headers, timeout=10)
    envs = r.json().get('data', []) or []
    matched = [e for e in envs if pin in (e.get('value') or '')]
    if matched:
        e = matched[0]
        r = requests.put(ql_url + 'api/envs', headers=headers, timeout=10,
                         json={'id': e['id'], 'name': 'JD_COOKIE', 'value': ck,
                               'remarks': '京东扫码登录'})
        return '更新' if r.json().get('code') == 200 else '更新失败'
    r = requests.post(ql_url + 'api/envs', headers=headers, timeout=10,
                      json=[{'name': 'JD_COOKIE', 'value': ck, 'remarks': '京东扫码登录'}])
    data = r.json()
    if data.get('code') == 200 and data.get('data'):
        ids = [d['id'] for d in data['data']]
        requests.put(ql_url + 'api/envs/enable', headers=headers, json=ids, timeout=10)
        return '新增'
    return '新增失败'


def main():
    print('京东扫码获取 Cookie（自动写入青龙环境变量）')
    s = requests.session()
    t = round(time.time())
    headers = {
        'User-Agent': jd_ua,
        'referer': 'https://plogin.m.jd.com/cgi-bin/mm/new_login_entrance?lang=chs&appid=300&returnurl=https://wq.jd.com/passport/LoginRedirect?state={0}&returnurl=https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'.format(t),
    }
    url = 'https://plogin.m.jd.com/cgi-bin/mm/new_login_entrance?lang=chs&appid=300&returnurl=https://wq.jd.com/passport/LoginRedirect?state={0}&returnurl=https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'.format(t)
    res = s.get(url=url, headers=headers, verify=False, timeout=15)
    s_token = json.loads(res.text)['s_token']

    t = round(time.time() * 1000)
    headers = {
        'User-Agent': jd_ua,
        'referer': 'https://plogin.m.jd.com/login/login?appid=300&returnurl=https://wqlogin2.jd.com/passport/LoginRedirect?state={0}&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'.format(t),
        'Content-Type': 'application/x-www-form-urlencoded; Charset=UTF-8',
    }
    url = 'https://plogin.m.jd.com/cgi-bin/m/tmauthreflogurl?s_token={0}&v={1}&remember=true'.format(s_token, t)
    data = {
        'lang': 'chs',
        'appid': 300,
        'returnurl': 'https://wqlogin2.jd.com/passport/LoginRedirect?state={0}returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'.format(t),
    }
    res = s.post(url=url, headers=headers, data=data, verify=False, timeout=15)
    token = json.loads(res.text)['token']
    okl_token = s.cookies.get_dict()['okl_token']
    qrurl = 'https://plogin.m.jd.com/cgi-bin/m/tmauth?client_type=m&appid=300&token={0}'.format(token)

    print('')
    print('请打开下面的链接显示二维码，用京东App扫码登录：')
    print('https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={0}'.format(qrurl))
    print('（如上面的图片链接打不开，可把下面这个链接复制到 cli.im 等二维码生成网站）')
    print(qrurl)
    print('')

    # 轮询等待扫码（最长约 5 分钟）
    for i in range(100):
        t = round(time.time() * 1000)
        headers = {
            'User-Agent': jd_ua,
            'referer': 'https://plogin.m.jd.com/login/login?appid=300&returnurl=https://wqlogin2.jd.com/passport/LoginRedirect?state={0}&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'.format(t),
            'Content-Type': 'application/x-www-form-urlencoded; Charset=UTF-8',
        }
        url = 'https://plogin.m.jd.com/cgi-bin/m/tmauthchecktoken?&token={0}&ou_state=0&okl_token={1}'.format(token, okl_token)
        data = {
            'lang': 'chs',
            'appid': 300,
            'returnurl': 'https://wqlogin2.jd.com/passport/LoginRedirect?state={0}returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action'.format(t),
            'source': 'wq_passport',
        }
        res = s.post(url=url, headers=headers, data=data, verify=False, timeout=15)
        check = json.loads(res.text)
        code = check['errcode']
        if code == 0:
            print('扫码成功！')
            jd_ck = s.cookies.get_dict()
            ck = 'pt_key={0};pt_pin={1};'.format(jd_ck['pt_key'], jd_ck['pt_pin'])
            print('获取到 Cookie: {0}'.format(ck))
            try:
                result = ql_save_cookie(ck, jd_ck['pt_pin'])
                print('已自动写入青龙环境变量 JD_COOKIE（{0}）'.format(result))
                print('现在可以去【定时任务】运行京豆签到脚本了')
            except Exception as e:
                print('自动写入失败：{0}'.format(e))
                print('请手动把上面的 Cookie 添加到青龙【环境变量】JD_COOKIE')
            return
        if i % 10 == 0 and i > 0:
            print('等待扫码中... ({0}秒)'.format(i * 3))
        time.sleep(3)
    print('超时未扫码，请重新运行本任务')


if __name__ == '__main__':
    main()
