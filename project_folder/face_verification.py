import cv2
import numpy as np
import os
import time
from datetime import datetime
from send_email import send_alert_email

# إعدادات المدرب
face_recognizer = cv2.face.LBPHFaceRecognizer_create()
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# مسارات المجلدات
KNOWN_FACES_DIR = 'dataset/known'
UNKNOWN_FACES_DIR = 'dataset/unknown'
ALERTS_DIR = 'alerts'

# إنشاء المجلدات إذا لم تكن موجودة
for directory in [KNOWN_FACES_DIR, UNKNOWN_FACES_DIR, ALERTS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def prepare_training_data():
    faces = []
    labels = []
    label_ids = {}
    current_id = 0
    
    # تحميل الوجوه المعروفة (المالك)
    person_name = "owner"  # يمكن تغيير هذا إذا كان لديك أكثر من شخص معروف
    person_dir = os.path.join(KNOWN_FACES_DIR, person_name)
    
    if not os.path.exists(person_dir):
        print(f"تحذير: مجلد {person_dir} غير موجود. قم بإضافة صور للمالك أولاً.")
        return None, None
    
    label_ids[person_name] = current_id
    
    for filename in os.listdir(person_dir):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            img_path = os.path.join(person_dir, filename)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            
            faces_detected = face_cascade.detectMultiScale(img, scaleFactor=1.1, minNeighbors=5)
            if len(faces_detected) == 1:
                x, y, w, h = faces_detected[0]
                face_roi = img[y:y+h, x:x+w]
                faces.append(face_roi)
                labels.append(current_id)
    
    # تدريب النموذج على الوجوه المعروفة فقط
    if len(faces) > 0:
        face_recognizer.train(faces, np.array(labels))
        print("تم تدريب النموذج على", len(faces), "صورة للشخص المعروف")
        return face_recognizer, label_ids
    else:
        print("لم يتم العثور على أي وجوه للتدريب")
        return None, None

def main():
    # تحضير البيانات وتدريب النموذج
    recognizer, label_ids = prepare_training_data()
    if recognizer is None:
        return
    
    # فتح الكاميرا
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    unknown_start_time = None
    alert_sent = False
    
    print("بدأ النظام. ضع وجهك أمام الكاميرا...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法捕获帧")
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        
        current_time = time.time()
        unknown_detected = False
        
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            
            # التعرف على الوجه
            label, confidence = recognizer.predict(face_roi)
            
            # إذا كان الثقة أقل من 70 (القيمة الأقل تعني تشابه أكبر)
            if confidence < 70:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, "معروف", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                unknown_start_time = None
                alert_sent = False
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "غير معروف", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                unknown_detected = True
                
                # بدء计时 لشخص غير معروف
                if unknown_start_time is None:
                    unknown_start_time = current_time
                    print("تم اكتشاف شخص غير معروف. بدء العد التنازلي...")
                
                # التحقق من مرور دقيقتين
                if unknown_start_time and (current_time - unknown_start_time) > 120 and not alert_sent:
                    # حفظ صورة للشخص غير المعروف
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    alert_filename = f"{ALERTS_DIR}/unknown_{timestamp}.jpg"
                    cv2.imwrite(alert_filename, frame)
                    print(f"تم حفظ صورة التنبيه: {alert_filename}")
                    
                    # إرسال البريد الإلكتروني
                    try:
                        send_alert_email(alert_filename)
                        print("تم إرسالة التنبيه بالبريد الإلكتروني")
                    except Exception as e:
                        print(f"خطأ في إرسال البريد الإلكتروني: {e}")
                    
                    alert_sent = True
        
        # إذا لم يتم اكتشاف أي وجوه غير معروفة، إعادة ضبط المؤقت
        if not unknown_detected:
            unknown_start_time = None
            alert_sent = False
        
        # عرض الإطار
        cv2.imshow('Face Verification', frame) 
        
        # الخروج عند الضغط على 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()