import requests
import time
import zipfile
import os
from pathlib import Path

api_key = 'eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIxODkwNDM1MCIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc0ODY5NjQ3MSwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiMTU4MDE0MzgzODYiLCJvcGVuSWQiOm51bGwsInV1aWQiOiIwYmNiYmU5NC0yMTliLTRiMjMtYjFiZi05ZWE5ZDZjZjQ0OTMiLCJlbWFpbCI6IiIsImV4cCI6MTc0OTkwNjA3MX0.CflSvU6KF09ZxYLrW9uzXAjK24VYaDh3WMEaDDGeTbbU17n4n3pSbc4zMaWpchEAwPiwuVGahb_ak7XjgK0dpw'

def upload_local_file_to_remote(local_file_path):
    """
    上传本地文件到临时存储并返回可访问的URL
    """
    import tempfile
    import uuid
    from datetime import datetime
    import hashlib
    
    # 验证本地文件是否存在
    if not os.path.exists(local_file_path):
        raise FileNotFoundError(f"本地文件不存在: {local_file_path}")
    
    # 验证是否为PDF文件
    if not str(local_file_path).lower().endswith('.pdf'):
        raise ValueError(f"文件不是PDF格式: {local_file_path}")
    
    # 生成一个唯一的文件标识符，基于文件内容和时间戳
    file_hash = hashlib.md5(open(local_file_path, 'rb').read()).hexdigest()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{file_hash}_{timestamp}_{Path(local_file_path).name}"
    
    # 尝试使用多个临时文件服务作为备选方案
    temp_upload_services = [
        {
            'url': 'https://file.io/',
            'method': 'POST',
            'file_param': 'file',
            'response_url_key': 'link'  # 在响应JSON中获取URL的键
        },
        {
            'url': 'https://uguu.se/upload.php',
            'method': 'POST',
            'file_param': 'files[]',
            'response_url_key': 'files.0.url'  # 假设返回格式
        },
        {
            'url': 'https://transfer.sh/',
            'method': 'POST',
            'file_param': 'file',
            'response_url_key': None  # 直接返回URL
        }
    ]
    
    for service in temp_upload_services:
        try:
            print(f"尝试使用 {service['url']} 上传文件...")
            with open(local_file_path, 'rb') as file:
                files = {service['file_param']: (unique_filename, file, 'application/pdf')}
                
                if service['url'] == 'https://uguu.se/upload.php':
                    # 这个服务可能需要特定的参数
                    response = requests.post(service['url'], files=files, data={'randomname': 'true'})
                else:
                    response = requests.post(service['url'], files=files)
            
            if response.status_code == 200:
                if service['response_url_key']:
                    # 解析JSON响应获取URL
                    try:
                        response_json = response.json()
                        # 简单处理键路径（如 'files.0.url'）
                        url_path = service['response_url_key'].split('.')
                        url = response_json
                        for key in url_path:
                            if key.isdigit():
                                url = url[int(key)]
                            else:
                                url = url[key]
                        remote_pdf_url = url.strip()
                    except:
                        # 如果JSON解析失败，返回原始响应
                        remote_pdf_url = response.text.strip()
                else:
                    # 直接使用响应文本作为URL
                    remote_pdf_url = response.text.strip()
                
                print(f"文件已成功上传到 {service['url']}: {remote_pdf_url}")
                return remote_pdf_url
            else:
                print(f"上传到 {service['url']} 失败，状态码: {response.status_code}")
                continue  # 尝试下一个服务
                
        except Exception as e:
            print(f"上传到 {service['url']} 失败: {e}")
            continue  # 尝试下一个服务
    
    # 如果所有临时服务都失败，使用备选方案
    print("所有临时上传服务都失败，使用备选方案...")
    return upload_to_temp_storage_fallback(local_file_path, unique_filename)


def upload_to_temp_storage_fallback(local_file_path, unique_filename):
    """
    备选的临时文件上传方法
    尝试使用阿里云OSS上传
    """
    print("正在尝试阿里云OSS上传...")
    return upload_to_oss(local_file_path, unique_filename)


def upload_to_oss(local_file_path, unique_filename=None):
    """
    上传文件到阿里云OSS
    需要用户提供OSS配置信息
    """
    try:
        import oss2
        
        # 检查是否提供了OSS配置
        # 在实际部署中，这些信息应该通过环境变量或配置文件提供
        oss_access_key_id = os.getenv('OSS_ACCESS_KEY_ID')
        oss_access_key_secret = os.getenv('OSS_ACCESS_KEY_SECRET')
        oss_endpoint = os.getenv('OSS_ENDPOINT', 'https://oss-cn-shanghai.aliyuncs.com')
        oss_bucket_name = os.getenv('OSS_BUCKET_NAME', 'vl-image')  # 根据代码中URL推断
        
        if not all([oss_access_key_id, oss_access_key_secret]):
            print("未配置阿里云OSS认证信息，使用环境变量OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET")
            print("正在尝试minerU直接上传...")
            return upload_to_mineru_direct(local_file_path)
        
        # 创建OSS认证
        auth = oss2.Auth(oss_access_key_id, oss_access_key_secret)
        bucket = oss2.Bucket(auth, oss_endpoint, oss_bucket_name)
        
        # 使用原始文件名或唯一文件名
        object_key = f"pdf/{Path(local_file_path).name}" if unique_filename is None else f"pdf/{unique_filename}"
        
        # 上传文件
        result = bucket.put_object_from_file(object_key, local_file_path)
        
        if result.status == 200:
            # 生成可访问的URL
            remote_pdf_url = f"https://{oss_bucket_name}.{oss_endpoint.replace('https://', '')}/{object_key}"
            print(f"文件已成功上传到OSS: {remote_pdf_url}")
            return remote_pdf_url
        else:
            print(f"OSS上传失败，状态码: {result.status}")
            return upload_to_mineru_direct(local_file_path)
            
    except ImportError:
        print("未安装oss2库，跳过OSS上传")
        return upload_to_mineru_direct(local_file_path)
    except Exception as e:
        print(f"OSS上传失败: {e}")
        return upload_to_mineru_direct(local_file_path)


def upload_to_mineru_direct(local_file_path):
    """
    尝试使用minerU的直接上传API
    """
    # 检查minerU是否支持直接上传文件（multipart/form-data格式）
    # 这种方式不需要预存文件到其他地方
    print("尝试使用minerU直接上传API...")
    
    file_name = Path(local_file_path).name
    task_creation_url = 'https://mineru.net/api/v4/extract/task'
    
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    with open(local_file_path, 'rb') as file:
        # 尝试使用multipart/form-data上传
        files = {'file': (file_name, file, 'application/pdf')}
        data = {
            'is_ocr': 'true',
            'enable_formula': 'false',
        }
        
        try:
            response = requests.post(task_creation_url, headers=headers, files=files, data=data)
        
            if response.status_code == 200:
                # 如果直接上传成功，返回任务ID而不是URL
                result = response.json()
                print(f"minerU API响应: {result}")
                
                if 'data' in result and 'task_id' in result['data']:
                    print("minerU直接上传成功")
                    # 返回一个特殊标识，表明使用了直接上传
                    return f"mineru_direct://{result['data']['task_id']}"
                else:
                    print(f"minerU直接上传API返回格式不符: {result}")
                    # 尝试使用URL上传方式
                    return upload_using_url_method(local_file_path)
            else:
                print(f"minerU直接上传失败，状态码: {response.status_code}, 响应: {response.text}")
                # 尝试使用URL上传方式
                return upload_using_url_method(local_file_path)
        except requests.exceptions.SSLError as ssl_err:
            print(f"SSL错误: {ssl_err}")
            print("尝试使用URL上传方式...")
            return upload_using_url_method(local_file_path)
        except Exception as e:
            print(f"minerU直接上传失败: {e}")
            return upload_using_url_method(local_file_path)


def upload_using_url_method(local_file_path):
    """
    使用URL方式上传（需要文件已存在于远程服务器）
    这是原始方法，但会先尝试一些公共URL服务
    """
    print("尝试URL方式上传...")
    
    # 尝试使用GitHub Gist或类似服务（需要用户配置认证）
    # 或者，可以使用简单的本地服务器方案，但这需要额外的设置
    # 作为临时方案，我们返回原始的URL格式，但提醒用户
    file_name = Path(local_file_path).name
    
    # 提供一个配置说明，让用户知道需要怎么设置
    print(f"注意：minerU API需要远程可访问的PDF URL")
    print(f"当前文件: {local_file_path}")
    print(f"需要将文件上传到公共服务器，URL格式类似: https://example.com/path/to/{file_name}")
    print(f"当前使用原始URL格式，但远程服务器上可能不存在该文件")
    
    original_url = 'https://vl-image.oss-cn-shanghai.aliyuncs.com/pdf/' + file_name
    return original_url

def get_task_id_from_local_file(local_file_path):
    """
    从本地文件路径处理PDF解析任务
    :param local_file_path: 本地PDF文件路径
    :return: 任务ID
    """
    # 首先尝试上传本地文件获取URL
    pdf_url = upload_local_file_to_remote(local_file_path)
    
    # 检查是否使用了minerU直接上传（特殊URL格式）
    if pdf_url.startswith("mineru_direct://"):
        # 直接从URL中提取任务ID
        task_id = pdf_url.replace("mineru_direct://", "")
        print(f"使用直接上传，任务ID: {task_id}")
        return task_id
    
    url = 'https://mineru.net/api/v4/extract/task'
    header = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        'url': pdf_url,
        'is_ocr': True,
        'enable_formula': False,
    }

    res = requests.post(url, headers=header, json=data)
    print(f"API响应状态码: {res.status_code}")
    
    if res.status_code != 200:
        print(f"API请求失败: {res.text}")
        return None
        
    response_json = res.json()
    print(f"API响应: {response_json}")
    
    if "data" not in response_json:
        print(f"API响应格式错误: {response_json}")
        return None
        
    task_id = response_json["data"]['task_id']
    print(f"获取到任务ID: {task_id}")
    return task_id

def get_task_id(file_name_or_path):
    """
    获取任务ID，兼容文件名或文件路径
    :param file_name_or_path: 文件名或完整路径
    :return: 任务ID
    """
    # 检查是否为本地文件路径
    if os.path.exists(file_name_or_path):
        return get_task_id_from_local_file(file_name_or_path)
    else:
        # 原始实现：直接使用文件名
        return get_original_task_id(file_name_or_path)

def get_original_task_id(file_name):
    """
    原始的get_task_id函数实现（适用于远程已存在文件）
    """
    url = 'https://mineru.net/api/v4/extract/task'
    header = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {api_key}"
    }
    pdf_url = 'https://vl-image.oss-cn-shanghai.aliyuncs.com/pdf/' + file_name
    data = {
        'url': pdf_url,
        'is_ocr': True,
        'enable_formula': False,
    }

    res = requests.post(url, headers=header, json=data)
    print(res.status_code)
    print(res.json())
    print(res.json()["data"])
    task_id = res.json()["data"]['task_id']
    return task_id

def get_result(task_id):
    """
    查询任务结果
    :param task_id: 任务ID
    """
    url = f'https://mineru.net/api/v4/extract/task/{task_id}'
    header = {
        'Content-Type': 'application/json',
        "Authorization": f"Bearer {api_key}"
    }

    while True:
        res = requests.get(url, headers=header)
        result = res.json()["data"]
        print(result)
        state = result.get('state')
        err_msg = result.get('err_msg', '')
        # 如果任务还在进行中，等待后重试
        if state in ['pending', 'running']:
            print("任务未完成，等待5秒后重试...")
            time.sleep(5)
            continue
        # 如果有错误，输出错误信息
        if err_msg:
            print(f"任务出错: {err_msg}")
            return
        # 如果任务完成，下载文件
        if state == 'done':
            full_zip_url = result.get('full_zip_url')
            if full_zip_url:
                local_filename = f"{task_id}.zip"
                print(f"开始下载: {full_zip_url}")
                r = requests.get(full_zip_url, stream=True)
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"下载完成，已保存到: {local_filename}")
                # 下载完成后自动解压
                unzip_file(local_filename)
            else:
                print("未找到 full_zip_url，无法下载。")
            return
        # 其他未知状态
        print(f"未知状态: {state}")
        return

# 解压zip文件的函数
def unzip_file(zip_path, extract_dir=None):
    """
    解压指定的zip文件到目标文件夹。
    :param zip_path: zip文件路径
    :param extract_dir: 解压目标文件夹，默认为zip同名目录
    """
    if extract_dir is None:
        extract_dir = zip_path.rstrip('.zip')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print(f"已解压到: {extract_dir}")

if __name__ == "__main__":
    # 示例：处理本地PDF文件
    local_pdf_path = './dummy_report.pdf'  # 替换为实际的本地PDF文件路径
    
    if os.path.exists(local_pdf_path):
        print(f"处理本地文件: {local_pdf_path}")
        task_id = get_task_id(local_pdf_path)
        print('task_id:', task_id)
        if task_id:
            get_result(task_id)
    else:
        # 使用原始方法处理远程文件
        file_name = '【财报】中芯国际：中芯国际2024年年度报告.pdf'
        task_id = get_task_id(file_name)
        print('task_id:', task_id)
        get_result(task_id)