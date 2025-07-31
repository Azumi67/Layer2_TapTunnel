![R (2)](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/a064577c-9302-4f43-b3bf-3d4f84245a6f)
نام پروژه :  تانل layer2-tap 
---------------------------------------------------------------
![check](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/13de8d36-dcfe-498b-9d99-440049c0cf14)
**امکانات**
- تانل سبک و لوکال layer2tap و udp tunneling
- قابلیت ویرایش تانل
- دارای ریست تایمر
- دارای گزینه حذف و نمایش status و logs

--------
![6348248](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/398f8b07-65be-472e-9821-631f7b70f783)
**آموزش نصب با اسکریپت**
 <div align="right">
  <details>
    <summary><strong><img src="https://github.com/Azumi67/Rathole_reverseTunnel/assets/119934376/fcbbdc62-2de5-48aa-bbdd-e323e96a62b5" alt="Image"> </strong>نصب تانل</summary>

------------------------------------ 
<p align="right">
  <img src="https://github.com/user-attachments/assets/e33e4570-ba53-4ed3-bfa8-46db026df4dc" alt="Image" />
</p>

- نام دیوایس را میدهم
- پرایوت ایپی ورژن 4 را با ساب نت 24 وارد میکنم
- پورت تانل را میدهم
<p align="right">
  <img src="https://github.com/user-attachments/assets/d303a1d1-1704-4e95-84ad-8dde4c2b3719" alt="Image" />
</p>

- نام دیوایس را میدهم
- ایپی مقابل پرایوت ایپی ورزن 4 که در سرور وارد کردم در اینجا وارد میکنم
- ایپی پابلیک سرور را میدهم
- پورت تانل را وارد میکنم
------------------

  </details>
  
--------------

![R (a2)](https://github.com/Azumi67/PrivateIP-Tunnel/assets/119934376/716fd45e-635c-4796-b8cf-856024e5b2b2)
**اسکریپت من**
----------------

- نصب پیش نیاز ها
```
apt install python3 -y && sudo apt install python3-pip &&  pip install colorama && pip install netifaces && apt install curl -y
pip3 install colorama
sudo apt-get install python-pip -y  &&  apt-get install python3 -y && alias python=python3 && python -m pip install colorama && python -m pip install netifaces
sudo apt update -y && sudo apt install -y python3 python3-pip curl && pip3 install --upgrade pip && pip3 install netifaces colorama requests

```
- اجرای اسکریپت
<div align="left">
  
```
apt install curl -y && bash -c "$(curl -fsSL https://raw.githubusercontent.com/Azumi67/Layer2_TapTunnel/refs/heads/main/tap.sh)"
```
