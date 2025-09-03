import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os

def send_alert_email(image_path):
    # إعدادات البريد الإلكتروني (يجب تعديلها حسب إعداداتك)
    sender_email = "hakimmh05@gmail.com"
    receiver_email = "ahma.ib2000@gmail.com"
    password = "bxvi ulgb tdzs vdfp"  # كلمة مرور التطبيق، وليس كلمة مرور البريد
    
    # إنشاء الرسالة
    msg = MIMEMultipart()
    msg['Subject'] = 'تحذير: تم اكتشاف شخص غير معروف'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    # نص الرسالة
    body = "تم اكتشاف شخص غير معروف أمام الكاميرا لأكثر من دقيقتين.\n\nهذه الصورة المرفقة تم التقاطها الآن."
    msg.attach(MIMEText(body, 'plain'))
    
    # إرفاق الصورة
    with open(image_path, 'rb') as f:
        img_data = f.read()
    image = MIMEImage(img_data, name=os.path.basename(image_path))
    msg.attach(image)
    
    # إرسال البريد
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, password)
        server.send_message(msg)