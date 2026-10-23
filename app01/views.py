from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import User
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import os
from django.conf import settings
import pandas as pd
import xgboost as xgb
import numpy as np
from joblib import load


# ================= 1. 登录视图 =================
def login(request):
    if request.method == 'POST':
        uid = request.POST.get('uid')
        psw = request.POST.get('psw')
        code = request.POST.get('code')

        if request.session.get('verify_code') != code.upper():
            return render(request, 'login.html', {'error_msg': '验证码错误！'})

        user = User.objects.filter(uid=uid, psw=psw).first()
        if user:
            request.session['info'] = {'uid': user.uid}
            return redirect('/index/')
        else:
            return render(request, 'login.html', {'error_msg': '用户名或密码错误！'})

    return render(request, 'login.html')


# ================= 2. 注册视图 =================
def register(request):
    if request.method == 'POST':
        uid = request.POST.get('uid')
        psw1 = request.POST.get('psw1')
        psw2 = request.POST.get('psw2')

        if User.objects.filter(uid=uid).exists():
            return render(request, 'register.html', {'error_msg': '用户名已存在！'})

        if psw1 != psw2:
            return render(request, 'register.html', {'error_msg': '两次输入的密码不一致！'})

        User.objects.create(uid=uid, psw=psw1)
        return redirect('/login/')

    return render(request, 'register.html')


# ================= 3. 验证码视图 =================
def get_verify_code(request):
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    code = ''.join(random.choices(chars, k=4))
    request.session['verify_code'] = code

    width, height = 120, 40
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()

    for i, char in enumerate(code):
        draw.text((10 + i * 25, 5), char, fill=(random.randint(0, 200), random.randint(0, 200), random.randint(0, 200)),
                  font=font)

    for _ in range(5):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    buf = BytesIO()
    img.save(buf, 'png')
    return HttpResponse(buf.getvalue(), content_type='image/png')


# ================= 4. 首页（上传）视图 =================
def index(request):
    if not request.session.get('info'):
        return redirect('/login/')

    if request.method == 'POST':
        my_file = request.FILES.get('file')
        if not my_file:
            return render(request, 'index.html', {'error_msg': '请选择要上传的文件！'})

        if not my_file.name.endswith('.csv'):
            return render(request, 'index.html', {'error_msg': '只能上传 CSV 格式的文件！'})

        save_path = os.path.join(settings.BASE_DIR, 'app01', 'pre_dataset.csv')
        with open(save_path, 'wb+') as destination:
            for chunk in my_file.chunks():
                destination.write(chunk)

        return redirect('/detection/')

    return render(request, 'index.html')


# ================= 5. 检测结果视图 =================
def detection(request):
    if not request.session.get('info'):
        return redirect('/login/')

    csv_path = os.path.join(settings.BASE_DIR, 'app01', 'pre_dataset.csv')
    model_path = os.path.join(settings.BASE_DIR, 'app01', 'models_dir', 'malware_detection.model')
    encoder_path = os.path.join(settings.BASE_DIR, 'app01', 'models_dir', 'label_encoder.joblib')

    try:
        test_df = pd.read_csv(csv_path)

        if 'Label' in test_df.columns:
            y_test = test_df['Label']
            X_test = test_df.drop('Label', axis=1)
            has_label = True
        else:
            X_test = test_df
            has_label = False

        loaded_model = xgb.Booster()
        loaded_model.load_model(model_path)

        label_encoder = load(encoder_path)

        dtest = xgb.DMatrix(X_test)
        predictions_prob = loaded_model.predict(dtest)
        predictions_binary = np.array([1 if pred > 0.5 else 0 for pred in predictions_prob])

        predicted_labels = label_encoder.inverse_transform(predictions_binary)

        results = []
        goodware_count = 0
        malware_count = 0


        # 先把真实标签也转换成数字（如果是文字的话）
        if has_label:
            if isinstance(y_test.iloc[0], str):
                # 如果数据是 'malware'/'goodware' 等文字，转成 0 和 1
                y_test_encoded = label_encoder.transform(y_test)
            else:
                # 如果本来就是 0 和 1，直接用
                y_test_encoded = y_test
        else:
            y_test_encoded = None

        for i in range(len(predicted_labels)):
            pred_label = predicted_labels[i]
            # 这里的真实标签，直接通过编码后的数字去反推，或者直接用数字
            if has_label:
                actual_label = label_encoder.inverse_transform([y_test_encoded.iloc[i]])[0]
            else:
                actual_label = "未知"



            if pred_label == 'goodware':
                goodware_count += 1
            else:
                malware_count += 1

            results.append({
                'id': i + 1,
                'predicted': pred_label,
                'actual': actual_label
            })

        accuracy = 0
        if has_label:
            # 预测值数字和真实值数字直接对比
            correct = sum(1 for i in range(len(predicted_labels)) if predictions_binary[i] == y_test_encoded.iloc[i])
            accuracy = round((correct / len(predicted_labels)) * 100, 2)

        chart_data = {
            'goodware': goodware_count,
            'malware': malware_count,
            'total': len(predicted_labels)
        }

        context = {
            'results': results[:20],
            'accuracy': accuracy,
            'chart_data': chart_data,
            'total_files': len(predicted_labels)
        }

        return render(request, 'detection.html', context)

    except Exception as e:
        return render(request, 'index.html', {'error_msg': f'检测失败，错误信息：{str(e)}'})