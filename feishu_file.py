"""
飞书文件上传模块
通过飞书应用 API 上传文件并发送到群聊
"""

import os
import requests
import config


def get_tenant_access_token():
    """获取 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": config.FEISHU_APP_ID,
        "app_secret": config.FEISHU_APP_SECRET
    }
    resp = requests.post(url, json=payload).json()
    return resp.get("tenant_access_token")


def upload_file(token, file_path):
    """
    上传文件到飞书，返回 file_key
    支持类型: doc, xls, ppt, pdf, zip, rar, stream 等
    HTML 文件用 stream 类型上传
    """
    url = "https://open.feishu.cn/open-apis/im/v1/files"
    headers = {"Authorization": f"Bearer {token}"}

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # 根据扩展名选择 file_type
    ext = os.path.splitext(file_name)[1].lower()
    type_map = {
        '.pdf': 'pdf',
        '.doc': 'doc', '.docx': 'doc',
        '.xls': 'xls', '.xlsx': 'xls',
        '.ppt': 'ppt', '.pptx': 'ppt',
    }
    file_type = type_map.get(ext, 'stream')

    with open(file_path, 'rb') as f:
        form_data = {
            'file_type': (None, file_type),
            'file_name': (None, file_name),
            'file': (file_name, f),
        }
        resp = requests.post(url, headers=headers, files=form_data).json()

    if resp.get('code') == 0:
        file_key = resp['data']['file_key']
        print(f"[INFO] 文件上传成功: {file_name} -> {file_key}")
        return file_key
    else:
        print(f"[ERROR] 文件上传失败: {resp.get('msg')} - {resp}")
        return None


def send_file_message(token, chat_id, file_key):
    """发送文件消息到群聊"""
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {"receive_id_type": "chat_id"}
    payload = {
        "receive_id": chat_id,
        "msg_type": "file",
        "content": f'{{"file_key": "{file_key}"}}'
    }

    resp = requests.post(url, headers=headers, params=params, json=payload).json()
    if resp.get('code') == 0:
        print(f"[INFO] 文件消息发送成功！")
        return True
    else:
        print(f"[ERROR] 文件消息发送失败: {resp.get('msg')} - {resp}")
        return False


def upload_and_send(file_path):
    """
    完整流程：上传文件 → 发送到群
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] 文件不存在: {file_path}")
        return False

    chat_id = getattr(config, 'FEISHU_FILE_CHAT_ID', '') or getattr(config, 'FEISHU_CHAT_ID', '')
    if not chat_id:
        print("[WARN] 未配置 FEISHU_FILE_CHAT_ID/FEISHU_CHAT_ID，跳过文件发送")
        return False

    token = get_tenant_access_token()
    if not token:
        print("[ERROR] 获取飞书 Token 失败")
        return False

    file_key = upload_file(token, file_path)
    if not file_key:
        return False

    return send_file_message(token, chat_id, file_key)
